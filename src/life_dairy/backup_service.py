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

from . import __version__ as APP_VERSION
from .logger import get_logger

logger = get_logger('backup_service')

BACKUP_TYPE = "LifeDiaryBackup"
KNOWN_MODULES = [
    "entries",
    "footprints",
    "books",
    "plans",
    "lessons",
    "self_analysis",
    "works",
    "thoughts",
    "resources",
    "observations",
]

MODULE_METADATA = {
    "entries": "entry.json",
    "footprints": "footprint.json",
    "books": "book.json",
    "plans": "plan.json",
    "lessons": "lesson.json",
    "self_analysis": "analysis.json",
    "works": "work.json",
    "thoughts": "thought.json",
    "resources": "resource.json",
    "observations": "observation.json",
}

MODULE_LABELS = {
    "entries": "日记",
    "footprints": "足迹",
    "books": "旧读书笔记",
    "plans": "轻计划 / 减法计划",
    "lessons": "教训反思",
    "self_analysis": "自我分析",
    "works": "作品感悟",
    "thoughts": "轻思考",
    "resources": "轻资源",
    "observations": "自我观察",
}


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

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    manifest = {
        "backup_type": BACKUP_TYPE,
        "app": "LifeDiary",
        "format_version": "1.0",
        "platform": "Desktop",
        "app_name": "人生档案 Diary",
        "backup_version": "1.0",
        "app_version": app_version,
        "created_at": now_str,
        "backup_time": now_str,
        "data_root": "Diary",
        "modules": [{"key": m, "title": MODULE_LABELS.get(m, m), "folder": f"{m}/"} for m in modules],
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

    logger.info(f"备份文件已创建: {zip_path.name}, {len(modules)} 个模块")
    return zip_path


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



def validate_backup(zip_path: Path | str) -> tuple[bool, str]:
    zip_path = Path(zip_path)
    if not zip_path.exists():
        logger.warning("备份文件不存在: %s", zip_path)
        return False, f"备份文件不存在：{zip_path}"

    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            names = archive.namelist()
            if "manifest.json" not in names:
                return False, "备份包缺少 manifest.json"

            try:
                manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                logger.warning("备份包 manifest.json 无法解析: %s", zip_path)
                return False, "manifest.json 无法读取或不是合法 JSON"

            # 兼容旧版 backup_type 和新版 format_version + app
            is_valid_format = (
                manifest.get("backup_type") == BACKUP_TYPE
                or (manifest.get("format_version") == "1.0" and manifest.get("app") == "LifeDiary")
            )
            if not is_valid_format:
                logger.warning("备份包 manifest 格式不匹配: %s", zip_path)
                return False, "manifest.json 格式不正确（需要 LifeDiary 格式）"

            if not any(name == "Diary/" or name.startswith("Diary/") for name in names):
                logger.warning("备份包缺少 Diary/ 目录: %s", zip_path)
                return False, "备份包中缺少 Diary/ 数据目录"

            if not _has_known_module(names):
                logger.warning("备份包无可识别数据模块: %s", zip_path)
                return False, "Diary/ 下没有可识别的数据模块目录"

            for name in names:
                if not _is_safe_zip_name(name):
                    logger.warning("备份包包含不安全路径: %s / %s", zip_path, name)
                    return False, f"备份包包含不安全路径：{name}"

    except zipfile.BadZipFile:
        logger.warning("文件不是合法 zip 备份包: %s", zip_path)
        return False, "文件不是合法 zip 备份包"
    except OSError as exc:
        logger.warning("读取备份包失败: %s - %s", zip_path, exc)
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
                logger.warning("恢复过程中出错，清理 data_root")
                _remove_tree(data_root)
            raise
    except Exception:
        logger.exception(f"恢复备份失败: {zip_path}")
        raise
    finally:
        _remove_tree(temp_dir)

    logger.info(f"备份恢复完成，安全备份: {safety_backup_path.name}")
    return safety_backup_path


def validate_mobile_backup(zip_path: Path | str) -> tuple[bool, str, dict]:
    zip_path = Path(zip_path)
    if not zip_path.exists():
        return False, f"数据包不存在：{zip_path}", {}
    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            names = archive.namelist()
            if not all(_is_safe_zip_name(name) for name in names):
                return False, "数据包里包含不安全路径。", {}
            if "manifest.json" not in names:
                return False, "数据包缺少 manifest.json。", {}
            try:
                manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return False, "manifest.json 不是合法 JSON。", {}
            if not any(name == "Diary/" or name.startswith("Diary/") for name in names):
                return False, "数据包里没有 Diary/ 数据目录。", manifest
            if not _has_known_module(names):
                return False, "Diary/ 里没有可识别的数据模块。", manifest
            return True, "OK", manifest
    except zipfile.BadZipFile:
        return False, "文件不是合法 ZIP。", {}
    except OSError as exc:
        return False, f"读取数据包失败：{exc}", {}


def import_mobile_backup(
    zip_path: Path | str,
    data_root: Path | str,
    safety_backup_dir: Path | str,
    app_version: str = APP_VERSION,
) -> tuple[Path, dict[str, int], dict]:
    zip_path = Path(zip_path)
    data_root = Path(data_root)
    safety_backup_dir = Path(safety_backup_dir)

    valid, message, manifest = validate_mobile_backup(zip_path)
    if not valid:
        raise ValueError(message)

    safety_backup_dir.mkdir(parents=True, exist_ok=True)
    safety_backup_path = create_backup(
        data_root,
        safety_backup_dir,
        app_version=app_version,
        filename_prefix="BeforeMobileImportBackup",
    )

    parent_dir = data_root.parent
    temp_dir = parent_dir / f"life_diary_mobile_import_{uuid4().hex}"
    temp_dir.mkdir(parents=True, exist_ok=False)
    stats: dict[str, int] = {
        "imported": 0,
        "updated": 0,
        "skipped": 0,
        "images": 0,
    }
    for module in KNOWN_MODULES:
        stats[module] = 0

    try:
        extract_dir = temp_dir / "extracted"
        extract_dir.mkdir()
        with zipfile.ZipFile(zip_path, "r") as archive:
            _safe_extract(archive, extract_dir)

        source_root = extract_dir / "Diary"
        if not source_root.exists() or not source_root.is_dir():
            raise ValueError("数据包中没有可导入的 Diary/ 目录。")

        data_root.mkdir(parents=True, exist_ok=True)
        _merge_diary_tree(source_root, data_root, stats)
    except Exception:
        logger.exception(f"导入手机版数据失败，尝试恢复: {safety_backup_path.name}")
        try:
            restore_backup(safety_backup_path, data_root, safety_backup_dir, app_version)
        finally:
            _remove_tree(temp_dir)
        raise

    _remove_tree(temp_dir)
    logger.info(f"手机版数据导入完成: 新增 {stats.get('imported',0)} 条，更新 {stats.get('updated',0)} 条")
    return safety_backup_path, stats, manifest


def format_import_stats(stats: dict[str, int], manifest: dict | None = None) -> str:
    lines = []
    manifest = manifest or {}
    source = manifest.get("platform") or manifest.get("source_platform") or manifest.get("app") or "未知来源"
    backup_time = manifest.get("backup_time") or manifest.get("created_at") or "未知时间"
    lines.append(f"来源：{source}")
    lines.append(f"备份时间：{backup_time}")
    lines.append(f"新增：{stats.get('imported', 0)} 条，更新：{stats.get('updated', 0)} 条，跳过：{stats.get('skipped', 0)} 条")
    if stats.get("images", 0):
        lines.append(f"图片：{stats.get('images', 0)} 个")
    module_parts = []
    for module in KNOWN_MODULES:
        count = stats.get(module, 0)
        if count:
            module_parts.append(f"{MODULE_LABELS.get(module, module)} {count} 条")
    lines.append("模块明细：" + ("；".join(module_parts) if module_parts else "没有新增或更新记录"))
    return "\n".join(lines)


def count_module_records(data_root: Path | str) -> dict[str, int]:
    data_root = Path(data_root)
    result: dict[str, int] = {}
    for module, metadata_name in MODULE_METADATA.items():
        module_dir = data_root / module
        count = 0
        if module_dir.exists() and module_dir.is_dir():
            for child in module_dir.iterdir():
                if not child.is_dir():
                    continue
                metadata_path = child / metadata_name
                if not metadata_path.exists():
                    continue
                try:
                    data = json.loads(metadata_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                if not data.get("deleted"):
                    count += 1
        result[module] = count
    return result


def run_data_health_check(data_root: Path | str) -> list[tuple[str, str]]:
    data_root = Path(data_root)
    results: list[tuple[str, str]] = []
    if data_root.exists() and data_root.is_dir():
        results.append(("正常", f"数据目录存在：{data_root}"))
    else:
        results.append(("错误", f"数据目录不存在：{data_root}"))
        return results

    manifest_path = data_root / "manifest.json"
    if manifest_path.exists():
        ok, message = _check_json_file(manifest_path)
        results.append(("正常" if ok else "错误", f"manifest.json：{message}"))
    else:
        results.append(("提示", "data/Diary/ 下没有 manifest.json；桌面端平时不依赖它，ZIP 备份包会单独生成 manifest。"))

    counts = count_module_records(data_root)
    for module in KNOWN_MODULES:
        module_dir = data_root / module
        label = MODULE_LABELS.get(module, module)
        if module_dir.exists() and module_dir.is_dir():
            results.append(("正常", f"{label}目录存在，当前可用记录 {counts.get(module, 0)} 条。"))
            images_dir_exists = any(child.is_dir() and (child / "images").exists() for child in module_dir.iterdir())
            if module in {"entries", "footprints", "books", "lessons", "self_analysis", "works"}:
                results.append(("正常" if images_dir_exists or counts.get(module, 0) == 0 else "提示", f"{label}图片目录检查完成。"))
        else:
            results.append(("提示", f"{label}目录暂不存在；没有该模块记录时这是正常的。"))

    for json_path in data_root.rglob("*.json"):
        ok, message = _check_json_file(json_path)
        if not ok:
            results.append(("错误", f"{json_path.relative_to(data_root)}：{message}"))
    if not any(level == "错误" for level, _message in results):
        results.append(("正常", "JSON 文件解析检查通过，没有发现会阻断启动的问题。"))
    return results


def _discover_modules(data_root: Path) -> list[str]:
    return sorted(child.name for child in data_root.iterdir() if child.is_dir())


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
            logger.debug("无法删除临时文件（可能被占用），继续重试: %s", item_path)

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
    for module, metadata_name in MODULE_METADATA.items():
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
                logger.debug("无法读取元数据以标记已删除: %s", metadata_path)
                continue


def _merge_diary_tree(source_root: Path, data_root: Path, stats: dict[str, int]) -> None:
    for module, metadata_name in MODULE_METADATA.items():
        source_module = source_root / module
        if not source_module.exists() or not source_module.is_dir():
            continue
        target_module = data_root / module
        target_module.mkdir(parents=True, exist_ok=True)

        for source_record in sorted(source_module.iterdir()):
            if not source_record.is_dir():
                continue
            metadata_path = source_record / metadata_name
            if not metadata_path.exists():
                stats["skipped"] += 1
                continue
            record_id = _record_id_from_metadata(metadata_path, source_record.name)
            target_record = target_module / record_id
            if not target_record.exists():
                shutil.copytree(source_record, target_record)
                stats[module] += 1
                stats["imported"] += 1
                stats["images"] += _count_images(source_record)
                continue

            if _source_is_newer(source_record / metadata_name, target_record / metadata_name):
                _remove_tree(target_record)
                shutil.copytree(source_record, target_record)
                stats[module] += 1
                stats["updated"] += 1
                stats["images"] += _count_images(source_record)
            else:
                stats["skipped"] += 1


def _record_id_from_metadata(metadata_path: Path, fallback: str) -> str:
    try:
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback
    for key in ("id", "entry_id", "place_id", "book_id", "plan_id", "lesson_id", "analysis_id", "work_id"):
        value = str(data.get(key, "")).strip()
        if value:
            return value
    return fallback


def _source_is_newer(source_metadata: Path, target_metadata: Path) -> bool:
    source_time = _metadata_updated_at(source_metadata)
    target_time = _metadata_updated_at(target_metadata)
    if not target_time:
        return True
    if not source_time:
        return False
    return source_time > target_time


def _metadata_updated_at(metadata_path: Path) -> str:
    try:
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    return str(data.get("updated_at") or data.get("created_at") or "")


def _count_images(record_dir: Path) -> int:
    total = 0
    for image_dir in record_dir.rglob("images"):
        if not image_dir.is_dir():
            continue
        try:
            total += sum(1 for child in image_dir.iterdir() if child.is_file())
        except OSError:
            logger.debug("统计图片时无法读取目录: %s", image_dir)
            continue
    return total


def _check_json_file(path: Path) -> tuple[bool, str]:
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, f"JSON 格式错误：第 {exc.lineno} 行第 {exc.colno} 列"
    except OSError as exc:
        return False, f"读取失败：{exc}"
    return True, "可以解析"
