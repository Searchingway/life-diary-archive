"""Desktop Canonical / Mobile Working Copy synchronisation for Protocol V1."""
from __future__ import annotations

import hashlib
import difflib
import json
import os
import shutil
import subprocess
import threading
import uuid
import zipfile
from copy import deepcopy
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

import data_api
from plan_v2 import PLAN_SCHEMA_VERSION, migrate_plan_to_v2


PROTOCOL_VERSION = 1
SHARED_MODULES = ("entries", "footprints", "plans", "info_memos")
_LOCK = threading.RLock()


def _normalise_text(value: Any) -> str:
    lines = str(value or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return "\n".join(line.rstrip() for line in lines).strip()


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_zip_name(name: str) -> PurePosixPath:
    path = PurePosixPath(name.replace("\\", "/"))
    if not name or path.is_absolute() or ".." in path.parts or any(part in {"", "."} for part in path.parts):
        raise ValueError("unsafe ZIP path")
    if ":" in path.parts[0]:
        raise ValueError("unsafe ZIP path")
    return path


class SyncService:
    """Owns in-process staged sessions. No formal record is written until commit."""

    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}

    def prepare_mobile_import(self, zip_path: str | Path) -> dict[str, Any]:
        archive_path = Path(zip_path).expanduser().resolve()
        with _LOCK:
            manifest = self._preflight(archive_path)
            backup = self._create_safety_backup()
            session_id = uuid.uuid4().hex
            session_dir = data_api.DATA_ROOT.parent / ".sync_sessions" / session_id
            extracted = session_dir / "mobile_snapshot"
            self._extract_archive(archive_path, extracted)
            session: dict[str, Any] = {
                "id": session_id,
                "created_at": data_api.now_iso(),
                "manifest": manifest,
                "session_dir": str(session_dir),
                "safety_backup": str(backup),
                "summary": {key: 0 for key in ("new", "unchanged", "stale_mobile", "duplicate", "conflict")},
                "actions": [],
                "conflicts": [],
            }
            for source in self._source_records(extracted):
                self._stage_record(session, source)
            self._sessions[session_id] = session
            return self._public_session(session)

    def select_mobile_snapshot_zip(self) -> str:
        """Open the native desktop file picker; the browser never receives a raw path."""
        script = r'''
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Filter = 'ZIP archives (*.zip)|*.zip'
$dialog.Title = '选择手机版同步 ZIP'
if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { Write-Output $dialog.FileName }
'''
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            check=False,
            capture_output=True,
            text=True,
            timeout=300,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        selected = (result.stdout or "").strip().splitlines()
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "ZIP selection failed").strip())
        if not selected:
            raise ValueError("ZIP selection cancelled")
        return str(Path(selected[-1]).resolve())

    def get_session(self, session_id: str) -> dict[str, Any]:
        return self._public_session(self._session(session_id))

    def resolve_entry_conflict(self, session_id: str, conflict_id: str, body: str, title: str | None = None) -> dict[str, Any]:
        with _LOCK:
            conflict = self._conflict(session_id, conflict_id, "entries")
            conflict["resolved"] = True
            conflict["resolved_body"] = str(body)
            conflict["resolved_title"] = str(title) if title is not None else conflict["desktop"]["title"]
            return self._public_conflict(conflict)

    def resolve_generic_conflict(self, session_id: str, conflict_id: str, choice: str) -> dict[str, Any]:
        if choice not in {"desktop", "mobile"}:
            raise ValueError("choice must be desktop or mobile")
        with _LOCK:
            conflict = self._conflict(session_id, conflict_id, None)
            conflict["resolved"] = True
            conflict["choice"] = choice
            return self._public_conflict(conflict)

    def commit_import(self, session_id: str) -> dict[str, Any]:
        with _LOCK:
            session = self._session(session_id)
            unresolved = [item for item in session["conflicts"] if not item.get("resolved")]
            if unresolved:
                raise ValueError("unresolved conflicts block import commit")
            original_root = data_api.DATA_ROOT
            session_dir = Path(session["session_dir"])
            working_root = session_dir / "commit_data"
            rollback_root = session_dir / "pre_commit_data"
            if working_root.exists():
                shutil.rmtree(working_root)
            if original_root.exists():
                shutil.copytree(original_root, working_root)
            else:
                working_root.mkdir(parents=True)
            try:
                data_api.DATA_ROOT = working_root
                for action in session["actions"]:
                    if action["kind"] == "new":
                        self._apply_source(action["source"])
                for conflict in session["conflicts"]:
                    self._apply_resolved_conflict(conflict)
            finally:
                data_api.DATA_ROOT = original_root
            try:
                if original_root.exists():
                    if rollback_root.exists():
                        shutil.rmtree(rollback_root)
                    os.replace(original_root, rollback_root)
                os.replace(working_root, original_root)
            except Exception:
                if not original_root.exists() and rollback_root.exists():
                    os.replace(rollback_root, original_root)
                raise
            session["committed_at"] = data_api.now_iso()
            return {"ok": True, "id": session_id, "safety_backup": session["safety_backup"], "summary": deepcopy(session["summary"])}

    def create_desktop_canonical_zip(self, output_path: str | Path) -> str:
        target = Path(output_path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        manifest = {
            "app": "LifeDiary",
            "protocol_version": PROTOCOL_VERSION,
            "package_role": "desktop_canonical",
            "source_platform": "desktop",
            "created_at": data_api.now_iso(),
            "schema_versions": {"plans": PLAN_SCHEMA_VERSION},
        }
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            for key in SHARED_MODULES:
                module = data_api.MODULE_BY_KEY[key]
                module_root = data_api.DATA_ROOT / module.directory
                if not module_root.exists():
                    continue
                for path in module_root.rglob("*"):
                    if not path.is_file():
                        continue
                    name = PurePosixPath("Diary") / module.directory / path.relative_to(module_root).as_posix()
                    if key == "plans" and path.name == "plan.json":
                        archive.writestr(str(name), json.dumps(migrate_plan_to_v2(data_api.read_json(path)), ensure_ascii=False, indent=2))
                    else:
                        archive.write(path, str(name))
        return str(target)

    def _preflight(self, archive_path: Path) -> dict[str, Any]:
        if not archive_path.is_file() or archive_path.suffix.lower() != ".zip":
            raise ValueError("mobile snapshot must be a ZIP file")
        with zipfile.ZipFile(archive_path) as archive:
            names: set[str] = set()
            for item in archive.infolist():
                if item.is_dir():
                    continue
                name = str(_safe_zip_name(item.filename))
                if name in names:
                    raise ValueError("duplicate ZIP path")
                names.add(name)
            if "manifest.json" not in names:
                raise ValueError("manifest.json is required")
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("manifest must be an object")
        if manifest.get("protocol_version") == PROTOCOL_VERSION:
            if manifest.get("package_role") != "mobile_snapshot" or manifest.get("source_platform") != "mobile":
                raise ValueError("not a mobile snapshot")
            if manifest.get("app") != "LifeDiary":
                raise ValueError("unexpected app")
            return manifest
        if manifest.get("format") == "life-diary-archive" and manifest.get("version") == 1:
            return {
                "app": "LifeDiary",
                "protocol_version": PROTOCOL_VERSION,
                "package_role": "mobile_snapshot",
                "source_platform": "mobile",
                "created_at": str(manifest.get("created_at") or ""),
                "schema_versions": {"plans": 1},
                "legacy_manifest": True,
            }
        raise ValueError("unsupported sync manifest")

    def _extract_archive(self, archive_path: Path, target: Path) -> None:
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive_path) as archive:
            for item in archive.infolist():
                if item.is_dir():
                    continue
                relative = _safe_zip_name(item.filename)
                destination = data_api.ensure_child_path(target, *relative.parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(item) as source, destination.open("wb") as output:
                    shutil.copyfileobj(source, output)

    def _create_safety_backup(self) -> Path:
        backups = data_api.DATA_ROOT.parent / "sync_backups"
        backups.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        target = backups / f"desktop-before-mobile-import-{stamp}.zip"
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            if data_api.DATA_ROOT.exists():
                for path in data_api.DATA_ROOT.rglob("*"):
                    if path.is_file():
                        archive.write(path, str(PurePosixPath("Diary") / path.relative_to(data_api.DATA_ROOT).as_posix()))
        return target

    def _source_records(self, extracted: Path) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for key in SHARED_MODULES:
            module = data_api.MODULE_BY_KEY[key]
            module_root = extracted / "Diary" / module.directory
            if not module_root.exists():
                continue
            for metadata_path in module_root.glob(f"*/{module.json_file}"):
                raw = data_api.read_json(metadata_path)
                record_id = str(raw.get("id") or raw.get(f"{key[:-1]}_id") or metadata_path.parent.name)
                data_api.validate_safe_id(record_id)
                raw["id"] = record_id
                if key == "plans":
                    raw = migrate_plan_to_v2(raw)
                if key == "footprints":
                    self._normalise_footprint_visits(metadata_path.parent)
                records.append({"module": key, "id": record_id, "directory": str(metadata_path.parent), "data": raw})
        return records

    def _normalise_footprint_visits(self, record_dir: Path) -> None:
        for visit_path in record_dir.glob("visits/*/visit.json"):
            data = data_api.read_json(visit_path)
            if data:
                data["id"] = str(data.get("id") or data.get("visit_id") or visit_path.parent.name)
                data_api.write_json(visit_path, data)

    def _stage_record(self, session: dict[str, Any], source: dict[str, Any]) -> None:
        if source["module"] == "entries":
            self._stage_entry(session, source)
            return
        module = data_api.MODULE_BY_KEY[source["module"]]
        current_dir = data_api.DATA_ROOT / module.directory / source["id"]
        if not current_dir.exists():
            self._add_action(session, "new", source)
            return
        current_data = data_api.read_json(current_dir / module.json_file)
        if self._canonical_json(current_data) == self._canonical_json(source["data"]):
            self._add_action(session, "unchanged", source)
            return
        self._add_conflict(session, source, self._generic_snapshot(current_dir, module), "same ID shared-record content differs")

    def _stage_entry(self, session: dict[str, Any], source: dict[str, Any]) -> None:
        mobile = self._entry_snapshot(Path(source["directory"]), source["data"])
        local_dir = data_api.DATA_ROOT / "entries" / source["id"]
        desktop_dir = local_dir if local_dir.exists() else self._desktop_entry_for_date(mobile["date"])
        if desktop_dir is None:
            self._add_action(session, "new", source)
            return
        desktop = self._entry_snapshot(desktop_dir, data_api.read_json(desktop_dir / "entry.json"))
        if self._entries_equal(desktop, mobile):
            self._add_action(session, "unchanged" if desktop["id"] == mobile["id"] else "duplicate", source)
        elif desktop["id"] == mobile["id"] and self._mobile_is_stale(desktop, mobile):
            self._add_action(session, "stale_mobile", source)
        else:
            self._add_conflict(session, source, desktop, "same ID contains new mobile information" if desktop["id"] == mobile["id"] else "same date uses a different ID")

    def _desktop_entry_for_date(self, date_value: str) -> Path | None:
        for item in data_api.list_module_records("entries"):
            if str(item.get("date") or "") == date_value:
                return data_api.DATA_ROOT / "entries" / str(item["id"])
        return None

    def _entry_snapshot(self, directory: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        body_file = str(metadata.get("body_file") or "content.md")
        try:
            body_path = data_api.ensure_child_path(directory, data_api.validate_safe_file_name(body_file))
        except ValueError:
            body_path = directory / "content.md"
        body = body_path.read_text(encoding="utf-8", errors="replace") if body_path.exists() else str(metadata.get("body") or "")
        images: list[dict[str, str]] = []
        images_dir = directory / "images"
        if images_dir.exists():
            for path in images_dir.iterdir():
                if path.is_file():
                    images.append({"file_name": path.name, "hash": _file_hash(path)})
        return {
            "id": str(metadata.get("id") or directory.name),
            "date": str(metadata.get("date") or "")[:10],
            "title": str(metadata.get("title") or ""),
            "body": body,
            "updated_at": str(metadata.get("updated_at") or ""),
            "directory": str(directory),
            "images": images,
        }

    def _entries_equal(self, desktop: dict[str, Any], mobile: dict[str, Any]) -> bool:
        return (
            desktop["date"] == mobile["date"]
            and _normalise_text(desktop["title"]) == _normalise_text(mobile["title"])
            and _normalise_text(desktop["body"]) == _normalise_text(mobile["body"])
            and {item["hash"] for item in desktop["images"]} == {item["hash"] for item in mobile["images"]}
        )

    def _mobile_is_stale(self, desktop: dict[str, Any], mobile: dict[str, Any]) -> bool:
        mobile_body = _normalise_text(mobile["body"])
        desktop_body = _normalise_text(desktop["body"])
        return (
            desktop["date"] == mobile["date"]
            and _normalise_text(desktop["title"]) == _normalise_text(mobile["title"])
            and desktop_body.startswith(mobile_body)
            and {item["hash"] for item in mobile["images"]}.issubset({item["hash"] for item in desktop["images"]})
        )

    def _add_action(self, session: dict[str, Any], kind: str, source: dict[str, Any]) -> None:
        session["summary"][kind] += 1
        session["actions"].append({"kind": kind, "source": source})

    def _add_conflict(self, session: dict[str, Any], source: dict[str, Any], desktop: dict[str, Any], reason: str) -> None:
        mobile = self._entry_snapshot(Path(source["directory"]), source["data"]) if source["module"] == "entries" else self._generic_snapshot(Path(source["directory"]), data_api.MODULE_BY_KEY[source["module"]])
        conflict = {
            "id": uuid.uuid4().hex,
            "kind": "conflict",
            "module": source["module"],
            "canonical_id": str(desktop["id"]),
            "desktop": desktop,
            "mobile": mobile,
            "source": source,
            "reason": reason,
            "resolved": False,
        }
        session["summary"]["conflict"] += 1
        session["conflicts"].append(conflict)

    def _generic_snapshot(self, directory: Path, module: data_api.ModuleConfig) -> dict[str, Any]:
        data = data_api.read_json(directory / module.json_file)
        return {"id": str(data.get("id") or directory.name), "body": json.dumps(data, ensure_ascii=False, indent=2), "updated_at": str(data.get("updated_at") or ""), "directory": str(directory)}

    def _apply_source(self, source: dict[str, Any]) -> None:
        if source["module"] == "entries":
            mobile = self._entry_snapshot(Path(source["directory"]), source["data"])
            self._write_entry(mobile, mobile["id"], mobile["title"], mobile["body"])
            return
        self._copy_generic_source(source)

    def _apply_resolved_conflict(self, conflict: dict[str, Any]) -> None:
        if conflict["module"] != "entries":
            if conflict.get("choice") == "mobile":
                self._copy_generic_source(conflict["source"], target_id=conflict["canonical_id"])
            return
        desktop = conflict["desktop"]
        mobile = conflict["mobile"]
        self._write_entry(desktop, conflict["canonical_id"], conflict["resolved_title"], conflict["resolved_body"], mobile)

    def _write_entry(self, base: dict[str, Any], record_id: str, title: str, body: str, mobile: dict[str, Any] | None = None) -> None:
        data_api.save_entry({"id": record_id, "date": base["date"], "title": title, "body": body})
        record_dir = data_api.DATA_ROOT / "entries" / record_id
        metadata_path = record_dir / "entry.json"
        metadata = data_api.read_json(metadata_path)
        images_dir = record_dir / "images"
        images_dir.mkdir(exist_ok=True)
        retained: dict[str, str] = {
            _file_hash(path): path.name for path in images_dir.iterdir() if path.is_file()
        }
        for source in (base, mobile):
            if not source:
                continue
            source_dir = Path(source["directory"]) / "images"
            for item in source["images"]:
                content_hash = item["hash"]
                if content_hash in retained:
                    continue
                source_file = source_dir / item["file_name"]
                if not source_file.exists():
                    continue
                target_name = item["file_name"] if not (images_dir / item["file_name"]).exists() else data_api.unique_image_name(images_dir, item["file_name"])
                shutil.copy2(source_file, images_dir / target_name)
                retained[content_hash] = target_name
        metadata["images"] = [{"file_name": name, "label": ""} for name in retained.values()]
        metadata["updated_at"] = data_api.now_iso()
        data_api.write_json(metadata_path, metadata)

    def _copy_generic_source(self, source: dict[str, Any], target_id: str | None = None) -> None:
        module = data_api.MODULE_BY_KEY[source["module"]]
        record_id = target_id or source["id"]
        data_api.validate_safe_id(record_id)
        target = data_api.DATA_ROOT / module.directory / record_id
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(Path(source["directory"]), target)
        metadata_path = target / module.json_file
        metadata = data_api.read_json(metadata_path)
        metadata["id"] = record_id
        if source["module"] == "plans":
            metadata = migrate_plan_to_v2(metadata)
        data_api.write_json(metadata_path, metadata)

    def _canonical_json(self, value: dict[str, Any]) -> str:
        cleaned = {key: item for key, item in value.items() if key not in {"updated_at", "created_at"}}
        return json.dumps(cleaned, ensure_ascii=False, sort_keys=True)

    def _session(self, session_id: str) -> dict[str, Any]:
        if session_id not in self._sessions:
            raise FileNotFoundError("sync session not found")
        return self._sessions[session_id]

    def _conflict(self, session_id: str, conflict_id: str, module: str | None) -> dict[str, Any]:
        for conflict in self._session(session_id)["conflicts"]:
            if conflict["id"] == conflict_id and (module is None or conflict["module"] == module):
                return conflict
        raise FileNotFoundError("sync conflict not found")

    def _public_conflict(self, conflict: dict[str, Any]) -> dict[str, Any]:
        public = {key: deepcopy(value) for key, value in conflict.items() if key not in {"source"}}
        if conflict["module"] == "entries":
            desktop_lines = str(conflict["desktop"]["body"]).splitlines() or [""]
            mobile_lines = str(conflict["mobile"]["body"]).splitlines() or [""]
            matcher = difflib.SequenceMatcher(a=desktop_lines, b=mobile_lines)
            desktop_changed: set[int] = set()
            mobile_changed: set[int] = set()
            for tag, left_start, left_end, right_start, right_end in matcher.get_opcodes():
                if tag != "equal":
                    desktop_changed.update(range(left_start, left_end))
                    mobile_changed.update(range(right_start, right_end))
            public["desktop_changed_lines"] = sorted(desktop_changed)
            public["mobile_changed_lines"] = sorted(mobile_changed)
        return public

    def _public_session(self, session: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": session["id"],
            "created_at": session["created_at"],
            "manifest": deepcopy(session["manifest"]),
            "safety_backup": session["safety_backup"],
            "summary": deepcopy(session["summary"]),
            "conflicts": [self._public_conflict(item) for item in session["conflicts"]],
            "committed_at": session.get("committed_at"),
        }
