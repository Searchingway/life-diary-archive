from __future__ import annotations

import json
import os
import shutil
import stat
import time
import zipfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4


APP_VERSION = "2.6"
BACKUP_TYPE = "LifeDiaryBackup"
KNOWN_MODULES = ["entries", "footprints", "books", "plans", "lessons", "self_analysis"]


def create_backup(
    data_root: Path | str,
    output_dir: Path | str,
    app_version: str = APP_VERSION,
    filename_prefix: str = "DiaryBackup",
) -> Path:
    data_root = Path(data_root)
    output_dir = Path(output_dir)
    if not data_root.exists() or not data_root.is_dir():
        raise FileNotFoundError(f"数据目录不存在：{data_root}")

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    zip_path = _unique_backup_path(output_dir / f"{filename_prefix}_{timestamp}.zip")
    modules = _discover_modules(data_root)

    manifest = {
        "backup_type": BACKUP_TYPE,
        "app_name": "人生档案 Diary",
        "backup_version": "1.0",
        "app_version": app_version,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data_root": "Diary",
        "modules": modules,
    }

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        archive.writestr("Diary/", "")
        for path in sorted(data_root.rglob("*")):
            relative = path.relative_to(data_root)
            archive_name = Path("Diary") / relative
            if path.is_dir():
                archive.writestr(f"{archive_name.as_posix()}/", "")
            elif path.is_file():
                archive.write(path, archive_name.as_posix())

    return zip_path


def validate_backup(zip_path: Path | str) -> tuple[bool, str]:
    zip_path = Path(zip_path)
    if not zip_path.exists():
        return False, f"备份文件不存在：{zip_path}"

    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            names = archive.namelist()
            if "manifest.json" not in names:
                return False, "备份包缺少 manifest.json"

            try:
                manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return False, "manifest.json 无法读取或不是合法 JSON"

            if manifest.get("backup_type") != BACKUP_TYPE:
                return False, "manifest.json 中 backup_type 不正确"

            if not any(name == "Diary/" or name.startswith("Diary/") for name in names):
                return False, "备份包中缺少 Diary/ 数据目录"

            if not _has_known_module(names):
                return False, "Diary/ 下没有可识别的数据模块目录"

            for name in names:
                if not _is_safe_zip_name(name):
                    return False, f"备份包包含不安全路径：{name}"

    except zipfile.BadZipFile:
        return False, "文件不是合法 zip 备份包"
    except OSError as exc:
        return False, f"读取备份包失败：{exc}"

    return True, "OK"


def restore_backup(
    zip_path: Path | str,
    data_root: Path | str,
    safety_backup_dir: Path | str,
    app_version: str = APP_VERSION,
) -> Path:
    zip_path = Path(zip_path)
    data_root = Path(data_root)
    safety_backup_dir = Path(safety_backup_dir)

    valid, message = validate_backup(zip_path)
    if not valid:
        raise ValueError(message)

    safety_backup_dir.mkdir(parents=True, exist_ok=True)
    safety_backup_path = create_backup(
        data_root,
        safety_backup_dir,
        app_version=app_version,
        filename_prefix="BeforeRestoreBackup",
    )

    parent_dir = data_root.parent
    parent_dir.mkdir(parents=True, exist_ok=True)
    restored = False

    temp_dir = parent_dir / f"life_diary_restore_{uuid4().hex}"
    temp_dir.mkdir(parents=True, exist_ok=False)
    try:
        extract_dir = temp_dir / "extracted"
        extract_dir.mkdir()

        with zipfile.ZipFile(zip_path, "r") as archive:
            _safe_extract(archive, extract_dir)

        extracted_diary = extract_dir / "Diary"
        if not extracted_diary.exists() or not extracted_diary.is_dir():
            raise ValueError("备份包中没有可恢复的 Diary/ 目录")

        replacement_root = temp_dir / "Diary_replacement"
        shutil.copytree(extracted_diary, replacement_root)

        try:
            if data_root.exists():
                _remove_tree(data_root)
                if data_root.exists():
                    _overlay_restore(replacement_root, data_root)
                else:
                    shutil.copytree(replacement_root, data_root)
            else:
                shutil.copytree(replacement_root, data_root)
            restored = True
        except Exception:
            if data_root.exists() and not restored:
                _remove_tree(data_root)
            raise
    finally:
        _remove_tree(temp_dir)

    return safety_backup_path


def _discover_modules(data_root: Path) -> list[str]:
    return sorted(child.name for child in data_root.iterdir() if child.is_dir())


def _unique_backup_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    counter = 1
    while True:
        candidate = path.with_name(f"{stem}_{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def _has_known_module(names: list[str]) -> bool:
    for module in KNOWN_MODULES:
        prefix = f"Diary/{module}/"
        if any(name == prefix or name.startswith(prefix) for name in names):
            return True
    return False


def _is_safe_zip_name(name: str) -> bool:
    path = Path(name)
    if path.is_absolute():
        return False
    return ".." not in path.parts


def _safe_extract(archive: zipfile.ZipFile, target_dir: Path) -> None:
    target_root = target_dir.resolve()
    for member in archive.infolist():
        if not _is_safe_zip_name(member.filename):
            raise ValueError(f"备份包包含不安全路径：{member.filename}")
        destination = (target_dir / member.filename).resolve()
        if destination != target_root and target_root not in destination.parents:
            raise ValueError(f"备份包包含越界路径：{member.filename}")
        archive.extract(member, target_dir)


def _move_path(source: Path, target: Path) -> None:
    last_error: Exception | None = None
    for _attempt in range(8):
        try:
            if target.exists():
                _remove_tree(target)
            source.rename(target)
            return
        except OSError as exc:
            last_error = exc
            time.sleep(0.15)
    if last_error is not None:
        raise last_error


def _remove_tree(path: Path) -> None:
    if not path.exists():
        return

    def on_error(function, item_path, _exc_info) -> None:
        try:
            os.chmod(item_path, stat.S_IWRITE)
            function(item_path)
        except OSError:
            pass

    for _attempt in range(8):
        shutil.rmtree(path, onerror=on_error)
        if not path.exists():
            return
        time.sleep(0.15)
    shutil.rmtree(path, ignore_errors=True)


def _overlay_restore(source_root: Path, data_root: Path) -> None:
    _soft_hide_existing_known_records(source_root, data_root)
    shutil.copytree(source_root, data_root, dirs_exist_ok=True)


def _soft_hide_existing_known_records(source_root: Path, data_root: Path) -> None:
    metadata_names = {
        "entries": "entry.json",
        "footprints": "footprint.json",
        "books": "book.json",
        "plans": "plan.json",
        "lessons": "lesson.json",
    }
    for module, metadata_name in metadata_names.items():
        current_module = data_root / module
        if not current_module.exists():
            continue
        restored_ids = {
            child.name
            for child in (source_root / module).iterdir()
            if child.is_dir()
        } if (source_root / module).exists() else set()
        for child in current_module.iterdir():
            if not child.is_dir() or child.name in restored_ids:
                continue
            metadata_path = child / metadata_name
            if not metadata_path.exists():
                continue
            try:
                data = json.loads(metadata_path.read_text(encoding="utf-8"))
                data["deleted"] = True
                data["deleted_at"] = datetime.now().astimezone().isoformat(timespec="microseconds")
                data["updated_at"] = data["deleted_at"]
                metadata_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            except (OSError, json.JSONDecodeError):
                continue
