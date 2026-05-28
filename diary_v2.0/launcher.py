from __future__ import annotations

import json
import mimetypes
import os
import base64
import re
import shutil
import subprocess
import sys
import threading
import uuid
import webbrowser
from dataclasses import dataclass
from datetime import date, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

sys.path.insert(0, str((Path(__file__).resolve().parent.parent / "src").resolve()))

from life_dairy.exporters import DiaryExporter, DiaryExportItem
from life_dairy.models import DiaryEntry, DiaryImage

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView


APP_TITLE = "人生档案 Diary Desktop 2.0"
BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
FRONTEND_DIST = BASE_DIR / "Untitled" / "dist"
LEGACY_DATA_ROOT = (REPO_ROOT / "data" / "Diary").resolve()
DATA_ROOT = Path(os.environ.get("LIFE_DIARY_DATA_ROOT", BASE_DIR / "data" / "Diary")).resolve()
MIGRATION_MARKER = DATA_ROOT / ".life_diary_2_migration.json"


@dataclass(frozen=True)
class ModuleConfig:
    key: str
    label: str
    directory: str
    json_file: str
    title_fields: tuple[str, ...]
    body_files: tuple[str, ...] = ()
    body_fields: tuple[str, ...] = ()
    date_fields: tuple[str, ...] = ("date", "due_date", "start_date", "created_at")
    type_fields: tuple[str, ...] = ("type", "plan_type", "work_type", "analysis_type", "info_type")
    status_fields: tuple[str, ...] = ("status", "priority")


MODULES: list[ModuleConfig] = [
    ModuleConfig("entries", "日记", "entries", "entry.json", ("title",), ("content.md",)),
    ModuleConfig("footprints", "足迹", "footprints", "footprint.json", ("place_name",), ("summary.md",)),
    ModuleConfig("plans", "轻计划", "plans", "plan.json", ("title",), body_fields=("notes", "reason", "alternative_action")),
    ModuleConfig("action_plans", "行动计划", "action_plans", "action_plan.json", ("title",), body_fields=("description", "summary")),
    ModuleConfig("thoughts", "轻思考", "thoughts", "thought.json", ("title",), body_fields=("description", "preliminary_conclusion", "notes")),
    ModuleConfig("resources", "轻资源", "resources", "resource.json", ("title",), body_fields=("description", "overall_judgement", "notes")),
    ModuleConfig("info_memos", "信息备忘", "info_memos", "info_memo.json", ("title",), body_fields=("main_content", "notes", "description")),
    ModuleConfig("observations", "自我观察", "observations", "observation.json", ("title", "scene"), body_fields=("description", "body", "notes")),
    ModuleConfig("lessons", "教训与反思", "lessons", "lesson.json", ("title",), ("event.md", "reflection.md"), ("summary", "cost")),
    ModuleConfig("self_analysis", "自我分析", "self_analysis", "analysis.json", ("title",), ("content.md",), ("summary", "analysis")),
    ModuleConfig("works", "作品感悟", "works", "work.json", ("title", "work_title"), ("content.md", "summary.md"), ("summary", "notes")),
    ModuleConfig("notes", "笔记", "notes", "note.json", ("title",), ("content.md",), ("content", "notes")),
]

MODULE_BY_KEY = {module.key: module for module in MODULES}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="microseconds")


def migrate_legacy_data_if_needed() -> bool:
    if os.environ.get("LIFE_DIARY_SKIP_MIGRATION") == "1":
        DATA_ROOT.mkdir(parents=True, exist_ok=True)
        return False
    if MIGRATION_MARKER.exists():
        return False
    if DATA_ROOT.exists() and any(DATA_ROOT.iterdir()):
        return False
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    if not LEGACY_DATA_ROOT.exists():
        MIGRATION_MARKER.write_text(
            json.dumps(
                {
                    "migrated": False,
                    "reason": "legacy data root not found",
                    "legacy_data_root": str(LEGACY_DATA_ROOT),
                    "created_at": now_iso(),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return False
    for child in LEGACY_DATA_ROOT.iterdir():
        target = DATA_ROOT / child.name
        if child.is_dir():
            shutil.copytree(child, target, dirs_exist_ok=True)
        elif child.is_file():
            shutil.copy2(child, target)
    MIGRATION_MARKER.write_text(
        json.dumps(
            {
                "migrated": True,
                "legacy_data_root": str(LEGACY_DATA_ROOT),
                "data_root": str(DATA_ROOT),
                "created_at": now_iso(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return True


def first_text(data: dict[str, Any], fields: tuple[str, ...]) -> str:
    for field in fields:
        value = data.get(field)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        value = json.load(file)
    return value if isinstance(value, dict) else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_body(record_dir: Path, data: dict[str, Any], module: ModuleConfig) -> str:
    body_parts: list[str] = []
    candidates = list(module.body_files)
    body_file = data.get("body_file")
    if isinstance(body_file, str) and body_file not in candidates:
        candidates.insert(0, body_file)

    for filename in candidates:
        path = record_dir / filename
        if path.exists() and path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace").strip()
            if text:
                body_parts.append(text)

    for field in module.body_fields:
        value = data.get(field)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            body_parts.append(text)

    if module.key == "resources":
        for item in data.get("resource_items", []):
            if isinstance(item, dict):
                item_type = str(item.get("type") or item.get("label") or "").strip()
                item_value = str(item.get("value") or item.get("description") or "").strip()
                if item_type or item_value:
                    body_parts.append(f"{item_type}: {item_value}".strip(": "))

    return "\n\n".join(dict.fromkeys(body_parts))


def write_body(record_dir: Path, data: dict[str, Any], module: ModuleConfig, body: str) -> None:
    if module.body_files:
        filename = module.body_files[0]
        if module.key == "entries":
            data["body_file"] = filename
        elif module.key in {"footprints", "self_analysis", "works", "notes"}:
            if filename.endswith(".md"):
                field = "summary_file" if filename == "summary.md" else "content_file"
                data.setdefault(field, filename)
        (record_dir / filename).write_text(body, encoding="utf-8")
        return
    if module.body_fields:
        data[module.body_fields[0]] = body


def record_from_directory(module: ModuleConfig, record_dir: Path) -> dict[str, Any] | None:
    json_path = record_dir / module.json_file
    if not json_path.exists():
        return None
    try:
        data = read_json(json_path)
    except (OSError, json.JSONDecodeError):
        return None
    if data.get("deleted"):
        return None

    record_id = str(data.get("id") or record_dir.name)
    title = first_text(data, module.title_fields) or "未命名记录"
    date_text = first_text(data, module.date_fields)
    updated_at = str(data.get("updated_at") or data.get("created_at") or "")
    record_type = first_text(data, module.type_fields)
    status = first_text(data, module.status_fields)
    subtitle = " / ".join(part for part in (record_type, status) if part) or module.label

    return {
        "id": record_id,
        "title": title,
        "subtitle": subtitle,
        "body": read_body(record_dir, data, module),
        "date": date_text[:10] if len(date_text) >= 10 else date_text,
        "updated_at": updated_at,
        "status": status,
        "type": record_type,
        "extra": data,
    }


def list_module_records(module_key: str, query: str = "") -> list[dict[str, Any]]:
    module = MODULE_BY_KEY[module_key]
    module_dir = DATA_ROOT / module.directory
    module_dir.mkdir(parents=True, exist_ok=True)
    keyword = query.strip().lower()
    records: list[dict[str, Any]] = []

    for child in module_dir.iterdir():
        if not child.is_dir():
            continue
        record = record_from_directory(module, child)
        if not record:
            continue
        haystack = "\n".join(str(record.get(key, "")) for key in ("title", "subtitle", "body", "date")).lower()
        if keyword and keyword not in haystack:
            continue
        records.append(record)

    records.sort(key=lambda item: str(item.get("updated_at") or item.get("date") or ""), reverse=True)
    return records


def build_overview() -> dict[str, Any]:
    modules: list[dict[str, Any]] = []
    recent: list[dict[str, Any]] = []
    for module in MODULES:
        records = list_module_records(module.key)
        latest = records[0]["updated_at"][:10] if records and records[0].get("updated_at") else ""
        modules.append({"key": module.key, "label": module.label, "count": len(records), "latest": latest})
        for record in records[:5]:
            recent.append({**record, "module": module.label, "module_key": module.key})

    recent.sort(key=lambda item: str(item.get("updated_at") or item.get("date") or ""), reverse=True)
    return {
        "data_root": str(DATA_ROOT),
        "legacy_data_root": str(LEGACY_DATA_ROOT),
        "migrated_from_legacy": MIGRATION_MARKER.exists(),
        "dashboard_stats": build_dashboard_stats(),
        "modules": modules,
        "recent": recent[:20],
    }


def build_dashboard_stats() -> dict[str, int]:
    today = date.today()
    month_prefix = today.strftime("%Y-%m")
    year_prefix = today.strftime("%Y")
    entries = list_module_records("entries")
    light_plans = list_module_records("plans")
    action_plans = list_module_records("action_plans")

    month_entries = [entry for entry in entries if str(entry.get("date", "")).startswith(month_prefix)]
    year_entries = [entry for entry in entries if str(entry.get("date", "")).startswith(year_prefix)]

    def word_count(records: list[dict[str, Any]]) -> int:
        return sum(len(str(record.get("body", ""))) for record in records)

    def image_count(records: list[dict[str, Any]]) -> int:
        total = 0
        for record in records:
            extra = record.get("extra")
            if isinstance(extra, dict) and isinstance(extra.get("images"), list):
                total += len(extra["images"])
        return total

    def completed(record: dict[str, Any]) -> bool:
        status = str(record.get("status") or "")
        extra = record.get("extra") if isinstance(record.get("extra"), dict) else {}
        tasks = extra.get("tasks") if isinstance(extra, dict) else []
        if "完成" in status or status.lower() in {"completed", "done"}:
            return True
        if isinstance(tasks, list) and tasks:
            return all(isinstance(task, dict) and task.get("done") for task in tasks)
        return False

    def active(record: dict[str, Any]) -> bool:
        status = str(record.get("status") or "")
        return ("进行" in status) or status.lower() in {"active", "in_progress"} or not completed(record)

    def updated_in(record: dict[str, Any], prefix: str) -> bool:
        value = str(record.get("updated_at") or record.get("date") or "")
        return value.startswith(prefix)

    today_str = today.isoformat()
    today_pending = 0
    for plan in action_plans:
        extra = plan.get("extra") if isinstance(plan.get("extra"), dict) else {}
        tasks = extra.get("tasks") if isinstance(extra, dict) else []
        if isinstance(tasks, list):
            today_pending += sum(
                1
                for task in tasks
                if isinstance(task, dict)
                and str(task.get("date") or "") == today_str
                and not bool(task.get("done"))
            )

    return {
        "month_diary_count": len(month_entries),
        "month_diary_words": word_count(month_entries),
        "month_diary_images": image_count(month_entries),
        "month_completed_plans": sum(1 for plan in light_plans + action_plans if completed(plan) and updated_in(plan, month_prefix)),
        "year_diary_count": len(year_entries),
        "year_diary_words": word_count(year_entries),
        "year_diary_images": image_count(year_entries),
        "year_completed_plans": sum(1 for plan in light_plans + action_plans if completed(plan) and updated_in(plan, year_prefix)),
        "action_plan_count": len(action_plans),
        "active_action_plan_count": sum(1 for plan in action_plans if active(plan)),
        "today_pending_tasks": today_pending,
    }


def save_entry(payload: dict[str, Any]) -> dict[str, Any]:
    record_id = str(payload.get("id") or uuid.uuid4().hex)
    record_dir = DATA_ROOT / "entries" / record_id
    record_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = record_dir / "entry.json"
    existing = read_json(metadata_path) if metadata_path.exists() else {}
    timestamp = now_iso()
    data = {
        **existing,
        "id": record_id,
        "date": str(payload.get("date") or date.today().isoformat()),
        "title": str(payload.get("title") or ""),
        "images": existing.get("images", []),
        "created_at": existing.get("created_at") or timestamp,
        "updated_at": timestamp,
        "body_file": "content.md",
    }
    metadata_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (record_dir / "content.md").write_text(str(payload.get("body") or ""), encoding="utf-8")
    return record_from_directory(MODULE_BY_KEY["entries"], record_dir) or {}


def image_metadata(value: Any) -> tuple[str, str] | None:
    if isinstance(value, str):
        return value, ""
    if isinstance(value, dict):
        file_name = str(value.get("file_name") or value.get("name") or "")
        label = str(value.get("label") or "")
        if file_name:
            return file_name, label
    return None


def unique_image_name(images_dir: Path, original_name: str) -> str:
    candidate = Path(original_name).name or "image"
    stem = Path(candidate).stem or "image"
    suffix = Path(candidate).suffix or ".png"
    candidate = f"{stem}{suffix}"
    counter = 1
    while (images_dir / candidate).exists():
        candidate = f"{stem}_{counter}{suffix}"
        counter += 1
    return candidate


def add_entry_images(entry_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    record_dir = DATA_ROOT / "entries" / entry_id
    metadata_path = record_dir / "entry.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"entry not found: {entry_id}")
    images_dir = record_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    data = read_json(metadata_path)
    images = list(data.get("images", [])) if isinstance(data.get("images"), list) else []
    files = payload.get("files")
    if not isinstance(files, list):
        raise ValueError("files must be a list")

    for item in files:
        if not isinstance(item, dict):
            continue
        raw_data = str(item.get("data") or "")
        if "," in raw_data and raw_data.startswith("data:"):
            raw_data = raw_data.split(",", 1)[1]
        content = base64.b64decode(raw_data)
        file_name = unique_image_name(images_dir, str(item.get("name") or "image.png"))
        (images_dir / file_name).write_bytes(content)
        images.append({"file_name": file_name, "label": str(item.get("label") or "")})

    data["images"] = images
    data["updated_at"] = now_iso()
    write_json(metadata_path, data)
    return record_from_directory(MODULE_BY_KEY["entries"], record_dir) or {}


def entry_image_path(entry_id: str, image_name: str) -> Path:
    candidate = (DATA_ROOT / "entries" / entry_id / "images" / image_name).resolve()
    images_root = (DATA_ROOT / "entries" / entry_id / "images").resolve()
    if not str(candidate).startswith(str(images_root)):
        raise ValueError("invalid image path")
    if not candidate.exists():
        raise FileNotFoundError(f"image not found: {image_name}")
    return candidate


def export_entry_word_pdf(entry_id: str) -> dict[str, str]:
    record_dir = DATA_ROOT / "entries" / entry_id
    metadata_path = record_dir / "entry.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"entry not found: {entry_id}")
    data = read_json(metadata_path)
    body = (record_dir / str(data.get("body_file", "content.md"))).read_text(encoding="utf-8", errors="replace")
    images = []
    image_paths: list[Path] = []
    for value in data.get("images", []):
        parsed = image_metadata(value)
        if not parsed:
            continue
        file_name, label = parsed
        images.append(DiaryImage(file_name=file_name, label=label))
        path = record_dir / "images" / file_name
        if path.exists():
            image_paths.append(path)
    entry = DiaryEntry(
        id=str(data.get("id") or entry_id),
        date=str(data.get("date") or date.today().isoformat()),
        title=str(data.get("title") or ""),
        body=body,
        created_at=str(data.get("created_at") or now_iso()),
        updated_at=str(data.get("updated_at") or now_iso()),
        images=images,
    )
    export_dir = DATA_ROOT / "exports"
    exporter = DiaryExporter(export_dir)
    docx_path, pdf_path = exporter.export_entries_word_and_pdf(
        [DiaryExportItem(entry=entry, image_lookup=exporter._build_image_lookup(image_paths))]
    )
    return {"docx_path": str(docx_path), "pdf_path": str(pdf_path)}


def build_diary_export_item(record_dir: Path) -> DiaryExportItem | None:
    metadata_path = record_dir / "entry.json"
    if not metadata_path.exists():
        return None
    data = read_json(metadata_path)
    if data.get("deleted"):
        return None
    body_path = record_dir / str(data.get("body_file", "content.md"))
    body = body_path.read_text(encoding="utf-8", errors="replace") if body_path.exists() else ""
    images: list[DiaryImage] = []
    image_paths: list[Path] = []
    for value in data.get("images", []):
        parsed = image_metadata(value)
        if not parsed:
            continue
        file_name, label = parsed
        images.append(DiaryImage(file_name=file_name, label=label))
        path = record_dir / "images" / file_name
        if path.exists():
            image_paths.append(path)
    entry = DiaryEntry(
        id=str(data.get("id") or record_dir.name),
        date=str(data.get("date") or date.today().isoformat()),
        title=str(data.get("title") or ""),
        body=body,
        created_at=str(data.get("created_at") or now_iso()),
        updated_at=str(data.get("updated_at") or now_iso()),
        images=images,
    )
    return DiaryExportItem(
        entry=entry,
        image_lookup={path.name: path for path in image_paths},
    )


def select_export_directory() -> Path:
    default_dir = DATA_ROOT / "exports"
    default_dir.mkdir(parents=True, exist_ok=True)
    script = r"""
Add-Type -AssemblyName System.Windows.Forms
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = '选择日记导出目录'
$dialog.SelectedPath = $env:LIFE_DIARY_EXPORT_DEFAULT
$dialog.ShowNewFolderButton = $true
if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
    Write-Output $dialog.SelectedPath
}
"""
    env = os.environ.copy()
    env["LIFE_DIARY_EXPORT_DEFAULT"] = str(default_dir)
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        check=False,
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
    )
    selected = (result.stdout or "").strip().splitlines()
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "选择导出目录失败").strip())
    if not selected:
        raise ValueError("已取消选择导出目录")
    output_dir = Path(selected[-1]).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def export_all_entries_word_pdf(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    output_text = str((payload or {}).get("output_dir") or "").strip()
    output_dir = Path(output_text).expanduser().resolve() if output_text else select_export_directory()
    output_dir.mkdir(parents=True, exist_ok=True)

    export_items: list[DiaryExportItem] = []
    entries_dir = DATA_ROOT / "entries"
    entries_dir.mkdir(parents=True, exist_ok=True)
    for child in entries_dir.iterdir():
        if not child.is_dir():
            continue
        item = build_diary_export_item(child)
        if item is not None:
            export_items.append(item)
    if not export_items:
        raise ValueError("没有可导出的日记")

    exporter = DiaryExporter(output_dir)
    docx_path, pdf_path = exporter.export_entries_word_and_pdf(
        export_items,
        export_all=True,
    )
    return {
        "docx_path": str(docx_path),
        "pdf_path": str(pdf_path),
        "output_dir": str(output_dir),
        "count": len(export_items),
    }


def update_entry_images(entry_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    record_dir = DATA_ROOT / "entries" / entry_id
    metadata_path = record_dir / "entry.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"entry not found: {entry_id}")
    images_dir = record_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    requested = payload.get("images")
    if not isinstance(requested, list):
        raise ValueError("images must be a list")

    next_images: list[dict[str, str]] = []
    keep_names: set[str] = set()
    for item in requested:
        parsed = image_metadata(item)
        if not parsed:
            continue
        file_name, label = parsed
        image_path = entry_image_path(entry_id, file_name)
        if not image_path.exists():
            continue
        if file_name in keep_names:
            continue
        next_images.append({"file_name": file_name, "label": label.strip()})
        keep_names.add(file_name)

    data = read_json(metadata_path)
    data["images"] = next_images
    data["updated_at"] = now_iso()
    write_json(metadata_path, data)

    for child in images_dir.iterdir():
        if child.is_file() and child.name not in keep_names:
            child.unlink(missing_ok=True)

    return record_from_directory(MODULE_BY_KEY["entries"], record_dir) or {}


def save_resource(payload: dict[str, Any]) -> dict[str, Any]:
    record_id = str(payload.get("id") or uuid.uuid4().hex)
    record_dir = DATA_ROOT / "resources" / record_id
    record_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = record_dir / "resource.json"
    existing = read_json(metadata_path) if metadata_path.exists() else {}
    extra = payload.get("extra") if isinstance(payload.get("extra"), dict) else {}
    timestamp = now_iso()
    data = {
        **existing,
        **extra,
        "id": record_id,
        "title": str(payload.get("title") or ""),
        "description": str(payload.get("body") or ""),
        "type": str(extra.get("type") or payload.get("type") or existing.get("type") or "其他"),
        "status": str(extra.get("status") or payload.get("status") or existing.get("status") or "考虑中"),
        "resource_items": extra.get("resource_items") if isinstance(extra.get("resource_items"), list) else existing.get("resource_items", []),
        "overall_judgement": str(extra.get("overall_judgement") or existing.get("overall_judgement") or ""),
        "subjective_feeling": str(extra.get("subjective_feeling") or existing.get("subjective_feeling") or ""),
        "recurrence_test": extra.get("recurrence_test") if isinstance(extra.get("recurrence_test"), dict) else existing.get("recurrence_test", {}),
        "notes": str(extra.get("notes") or existing.get("notes") or ""),
        "related_diaries": existing.get("related_diaries", []),
        "related_thoughts": existing.get("related_thoughts", []),
        "related_self_analysis": existing.get("related_self_analysis", []),
        "created_at": existing.get("created_at") or timestamp,
        "updated_at": timestamp,
    }
    metadata_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return record_from_directory(MODULE_BY_KEY["resources"], record_dir) or {}


def save_generic_record(module_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    if module_key == "entries":
        return save_entry(payload)
    if module_key == "resources":
        return save_resource(payload)

    module = MODULE_BY_KEY[module_key]
    record_id = str(payload.get("id") or uuid.uuid4().hex)
    record_dir = DATA_ROOT / module.directory / record_id
    record_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = record_dir / module.json_file
    existing = read_json(metadata_path) if metadata_path.exists() else {}
    extra = payload.get("extra") if isinstance(payload.get("extra"), dict) else {}
    timestamp = now_iso()
    data = {
        **existing,
        **extra,
        "id": record_id,
        "created_at": existing.get("created_at") or extra.get("created_at") or timestamp,
        "updated_at": timestamp,
    }

    title_field = module.title_fields[0]
    data[title_field] = str(payload.get("title") or data.get(title_field) or "")

    date_value = str(payload.get("date") or "")
    if date_value:
        date_field = module.date_fields[0]
        data[date_field] = date_value

    if payload.get("type"):
        data[module.type_fields[0]] = str(payload.get("type"))
    if payload.get("status"):
        data[module.status_fields[0]] = str(payload.get("status"))

    write_body(record_dir, data, module, str(payload.get("body") or ""))
    if module.key == "footprints":
        data.setdefault("visit_ids", [])
        data.setdefault("images", [])
    if module.key == "action_plans":
        data.setdefault("tasks", [])
    if module.key == "plans":
        data.setdefault("tags", [])
        data.setdefault("plan_type", data.get("plan_type") or "add")

    write_json(metadata_path, data)
    return record_from_directory(module, record_dir) or {}


def delete_generic_record(module_key: str, record_id: str) -> None:
    module = MODULE_BY_KEY[module_key]
    metadata_path = DATA_ROOT / module.directory / record_id / module.json_file
    if not metadata_path.exists():
        raise FileNotFoundError(f"record not found: {record_id}")
    data = read_json(metadata_path)
    timestamp = now_iso()
    data["deleted"] = True
    data["deleted_at"] = timestamp
    data["updated_at"] = timestamp
    write_json(metadata_path, data)


class LifeDiaryHandler(BaseHTTPRequestHandler):
    server_version = "LifeDiary2/1.0"

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/overview":
            self.send_json(build_overview())
            return
        image_match = re.fullmatch(r"/api/modules/entries/([^/]+)/images/(.+)", parsed.path)
        if image_match:
            try:
                path = entry_image_path(unquote(image_match.group(1)), unquote(image_match.group(2)))
                self.send_file(path)
            except Exception as exc:  # noqa: BLE001 - app boundary
                self.send_error(HTTPStatus.NOT_FOUND, str(exc))
            return
        if parsed.path.startswith("/api/modules/"):
            module_key = unquote(parsed.path.removeprefix("/api/modules/"))
            if module_key not in MODULE_BY_KEY:
                self.send_error(HTTPStatus.NOT_FOUND, "unknown module")
                return
            query = parse_qs(parsed.query).get("q", [""])[0]
            self.send_json(list_module_records(module_key, query))
            return
        self.serve_frontend(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/actions/open-data-root":
            os.startfile(DATA_ROOT)  # type: ignore[attr-defined]
            self.send_json({"ok": True})
            return
        image_match = re.fullmatch(r"/api/modules/entries/([^/]+)/images", parsed.path)
        if image_match:
            try:
                self.send_json(add_entry_images(unquote(image_match.group(1)), self.read_json_body()))
            except Exception as exc:  # noqa: BLE001 - app boundary
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        if parsed.path == "/api/modules/entries/export-all":
            try:
                self.send_json(export_all_entries_word_pdf(self.read_json_body()))
            except Exception as exc:  # noqa: BLE001 - app boundary
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        export_match = re.fullmatch(r"/api/modules/entries/([^/]+)/export", parsed.path)
        if export_match:
            try:
                self.send_json(export_entry_word_pdf(unquote(export_match.group(1))))
            except Exception as exc:  # noqa: BLE001 - app boundary
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        if not parsed.path.startswith("/api/modules/"):
            self.send_error(HTTPStatus.NOT_FOUND, "unknown endpoint")
            return
        module_key = unquote(parsed.path.removeprefix("/api/modules/"))
        try:
            if module_key not in MODULE_BY_KEY:
                self.send_error(HTTPStatus.NOT_FOUND, "unknown module")
                return
            payload = self.read_json_body()
            self.send_json(save_generic_record(module_key, payload))
        except Exception as exc:  # noqa: BLE001 - this is the app boundary
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def do_PUT(self) -> None:
        parsed = urlparse(self.path)
        image_match = re.fullmatch(r"/api/modules/entries/([^/]+)/images", parsed.path)
        if image_match:
            try:
                self.send_json(update_entry_images(unquote(image_match.group(1)), self.read_json_body()))
            except Exception as exc:  # noqa: BLE001 - app boundary
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        self.send_error(HTTPStatus.NOT_FOUND, "unknown endpoint")

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/modules/"):
            self.send_error(HTTPStatus.NOT_FOUND, "unknown endpoint")
            return
        parts = [unquote(part) for part in parsed.path.removeprefix("/api/modules/").split("/") if part]
        if len(parts) != 2 or parts[0] not in MODULE_BY_KEY:
            self.send_error(HTTPStatus.NOT_FOUND, "unknown record")
            return
        try:
            delete_generic_record(parts[0], parts[1])
            self.send_json({"ok": True})
        except Exception as exc:  # noqa: BLE001 - this is the app boundary
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        value = json.loads(raw) if raw else {}
        if not isinstance(value, dict):
            raise ValueError("request body must be an object")
        return value

    def send_json(self, payload: Any) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_file(self, path: Path) -> None:
        content = path.read_bytes()
        mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def serve_frontend(self, request_path: str) -> None:
        if not FRONTEND_DIST.exists():
            self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "frontend dist not found; run npm run build")
            return
        relative = request_path.strip("/") or "index.html"
        target = (FRONTEND_DIST / relative).resolve()
        if not str(target).startswith(str(FRONTEND_DIST.resolve())) or not target.exists() or target.is_dir():
            target = FRONTEND_DIST / "index.html"
        content = target.read_bytes()
        mime = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def start_server() -> ThreadingHTTPServer:
    migrate_legacy_data_if_needed()
    server = ThreadingHTTPServer(("127.0.0.1", 0), LifeDiaryHandler)
    thread = threading.Thread(target=server.serve_forever, name="LifeDiary2Server", daemon=True)
    thread.start()
    return server


class MainWindow(QMainWindow):
    def __init__(self, url: str):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1320, 860)
        view = QWebEngineView(self)
        view.load(QUrl(url))
        self.setCentralWidget(view)


def main() -> int:
    server = start_server()
    url = f"http://127.0.0.1:{server.server_port}/"
    app = QApplication(sys.argv)
    window = MainWindow(url)
    window.show()
    result = app.exec()
    server.shutdown()
    return result


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        fallback = FRONTEND_DIST / "index.html"
        if fallback.exists():
            webbrowser.open(fallback.as_uri())
        raise
