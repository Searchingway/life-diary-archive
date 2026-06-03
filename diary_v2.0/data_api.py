from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
import zipfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote

# Ensure src/ is on sys.path so life_dairy.* is importable
_src = str((Path(__file__).resolve().parent.parent / "src").resolve())
if _src not in sys.path:
    sys.path.insert(0, _src)

from life_dairy.models import DiaryEntry, DiaryImage


APP_TITLE = "人生档案 Diary Desktop 2.0"
BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
FRONTEND_DIST = BASE_DIR / "Untitled" / "dist"
LEGACY_DATA_ROOT = (REPO_ROOT / "data" / "Diary").resolve()
DATA_ROOT = Path(os.environ.get("LIFE_DIARY_DATA_ROOT", BASE_DIR / "data" / "Diary")).resolve()
MIGRATION_MARKER = DATA_ROOT / ".life_diary_2_migration.json"
SETTINGS_PATH = DATA_ROOT / "config" / "app_settings.json"


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
    ModuleConfig("info_memos", "接单备忘", "info_memos", "info_memo.json", ("title",), body_fields=("main_content", "notes", "description")),
    ModuleConfig("observations", "自我观察", "observations", "observation.json", ("title", "scene"), body_fields=("description", "body", "notes")),
    ModuleConfig("lessons", "教训与反思", "lessons", "lesson.json", ("title",), ("event.md", "reflection.md"), ("summary", "cost")),
    ModuleConfig("self_analysis", "自我分析", "self_analysis", "analysis.json", ("title",), ("content.md",), ("summary", "analysis")),
    ModuleConfig("works", "作品感悟", "works", "work.json", ("title", "work_title"), ("content.md", "summary.md"), ("summary", "notes")),
    ModuleConfig("notes", "信息备忘", "notes", "note.json", ("title",), ("content.md",), ("content", "notes")),
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
                {"migrated": False, "reason": "legacy data root not found", "legacy_data_root": str(LEGACY_DATA_ROOT), "created_at": now_iso()},
                ensure_ascii=False, indent=2,
            ), encoding="utf-8",
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
            {"migrated": True, "legacy_data_root": str(LEGACY_DATA_ROOT), "data_root": str(DATA_ROOT), "created_at": now_iso()},
            ensure_ascii=False, indent=2,
        ), encoding="utf-8",
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_settings() -> dict[str, Any]:
    if SETTINGS_PATH.exists():
        try:
            return read_json(SETTINGS_PATH)
        except (OSError, json.JSONDecodeError):
            return {}
    return {}


def write_settings(data: dict[str, Any]) -> dict[str, Any]:
    settings = {**read_settings(), **data, "updated_at": now_iso()}
    write_json(SETTINGS_PATH, settings)
    return settings


def default_export_dir() -> Path:
    return (DATA_ROOT / "exports").resolve()


def configured_export_dir() -> Path:
    value = str(read_settings().get("export_dir") or "").strip()
    output_dir = Path(value).expanduser().resolve() if value else default_export_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


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
    if module.key == "footprints":
        data = {**data, "visits": read_footprint_visits(record_dir, data)}
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
    if module_key == "entries":
        records.sort(key=lambda item: (str(item.get("date") or ""), str(item.get("updated_at") or "")), reverse=True)
    else:
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
                1 for task in tasks
                if isinstance(task, dict) and str(task.get("date") or "") == today_str and not bool(task.get("done"))
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


def normalize_images(values: Any, url_builder: Any | None = None) -> list[dict[str, str]]:
    images: list[dict[str, str]] = []
    if not isinstance(values, list):
        return images
    for value in values:
        parsed = image_metadata(value)
        if not parsed:
            continue
        file_name, label = parsed
        image = {"file_name": file_name, "label": label}
        if url_builder is not None:
            image["url"] = str(url_builder(file_name))
        images.append(image)
    return images


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
    return DiaryExportItem(entry=entry, image_lookup={path.name: path for path in image_paths})


def select_export_directory() -> Path:
    default_dir = configured_export_dir()
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
        check=False, capture_output=True, text=True, timeout=300, env=env,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    selected = (result.stdout or "").strip().splitlines()
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "选择导出目录失败").strip())
    if not selected:
        raise ValueError("已取消选择导出目录")
    output_dir = Path(selected[-1]).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def select_and_store_export_directory() -> dict[str, str]:
    output_dir = select_export_directory()
    write_settings({"export_dir": str(output_dir)})
    return {"export_dir": str(output_dir)}


def safe_export_name(raw: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]+', "_", raw)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ._")
    return cleaned[:100] or "diary_export"


def unique_output_path(target: Path) -> Path:
    if not target.exists():
        return target
    counter = 1
    while True:
        candidate = target.with_name(f"{target.stem}_{counter}{target.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def unique_output_dir(target: Path) -> Path:
    if not target.exists():
        return target
    counter = 1
    while True:
        candidate = target.with_name(f"{target.name}_{counter}")
        if not candidate.exists():
            return candidate
        counter += 1


def format_extra_value(value: Any, indent: str = "") -> list[str]:
    lines: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if item in (None, "", [], {}):
                continue
            if isinstance(item, (dict, list)):
                lines.append(f"{indent}{key}:")
                lines.extend(format_extra_value(item, indent + "  "))
            else:
                lines.append(f"{indent}{key}: {item}")
    elif isinstance(value, list):
        for index, item in enumerate(value, start=1):
            if isinstance(item, (dict, list)):
                lines.append(f"{indent}{index}.")
                lines.extend(format_extra_value(item, indent + "  "))
            elif item not in (None, ""):
                lines.append(f"{indent}{index}. {item}")
    elif value not in (None, ""):
        lines.append(f"{indent}{value}")
    return lines


def module_record_export_lines(module: ModuleConfig, record: dict[str, Any], index: int) -> list[str]:
    body = str(record.get("body") or "").strip()
    lines = [
        f"{index}. {record.get('title') or '未命名记录'}",
        f"日期：{record.get('date') or '未设置'}",
        f"类型：{record.get('type') or record.get('subtitle') or module.label}",
        f"状态：{record.get('status') or '未设置'}",
        f"更新时间：{record.get('updated_at') or '未设置'}",
        f"字数：{len(body)}",
        "",
        body or "（正文为空）",
    ]
    extra = record.get("extra") if isinstance(record.get("extra"), dict) else {}
    detail_lines: list[str] = []
    if module.key == "footprints":
        visits = extra.get("visits") if isinstance(extra.get("visits"), list) else []
        for visit in visits:
            if not isinstance(visit, dict):
                continue
            detail_lines.append(f"- {visit.get('date') or '未设置日期'}")
            thought = str(visit.get("thought") or "").strip()
            if thought:
                detail_lines.append(f"  感想：{thought}")
            images = visit.get("images") if isinstance(visit.get("images"), list) else []
            if images:
                names = [label or file_name for image in images if (parsed := image_metadata(image)) and (file_name := parsed[0]) and (label := parsed[1]) or True]
                for img in images:
                    parsed = image_metadata(img)
                    if parsed:
                        file_name, label = parsed
                        names.append(label or file_name)
                if names:
                    detail_lines.append(f"  图片：{'、'.join(set(names))}")
    elif module.key == "action_plans":
        tasks = extra.get("tasks") if isinstance(extra.get("tasks"), list) else []
        for task in tasks:
            if not isinstance(task, dict):
                continue
            mark = "完成" if task.get("done") else "未完成"
            title = str(task.get("title") or "未命名子任务")
            task_date = str(task.get("date") or "").strip()
            task_time = str(task.get("time") or "").strip()
            note = str(task.get("note") or "").strip()
            detail_lines.append(f"- [{mark}] {title} {task_date} {task_time}".rstrip())
            if note:
                detail_lines.append(f"  备注：{note}")
    elif module.key == "resources":
        resource_items = extra.get("resource_items") if isinstance(extra.get("resource_items"), list) else []
        for item in resource_items:
            if not isinstance(item, dict):
                continue
            label = str(item.get("type") or item.get("label") or "").strip()
            value = str(item.get("value") or item.get("description") or "").strip()
            if label or value:
                detail_lines.append(f"- {label or '资源'}：{value}")
        judgement = str(extra.get("overall_judgement") or "").strip()
        if judgement:
            detail_lines.append(f"- 综合判断：{judgement}")
    elif module.key == "info_memos":
        fields = extra.get("type_fields") if isinstance(extra.get("type_fields"), dict) else {}
        detail_lines.extend(format_extra_value(fields))
    else:
        images = extra.get("images") if isinstance(extra.get("images"), list) else []
        if images:
            names = []
            for img in images:
                parsed = image_metadata(img)
                if parsed:
                    file_name, label = parsed
                    names.append(label or file_name)
            if names:
                detail_lines.append(f"图片：{'、'.join(names)}")
    if detail_lines:
        lines.extend(["", "补充信息：", *detail_lines])
    lines.extend(["", "-" * 48, ""])
    return lines


# --- Footprint operations ---

def read_footprint_visits(record_dir: Path, data: dict[str, Any]) -> list[dict[str, Any]]:
    visits_dir = record_dir / "visits"
    visits_dir.mkdir(parents=True, exist_ok=True)
    visit_ids = data.get("visit_ids") if isinstance(data.get("visit_ids"), list) else []
    candidates = [visits_dir / str(visit_id) for visit_id in visit_ids]
    candidates.extend(child for child in visits_dir.iterdir() if child.is_dir() and child not in candidates)
    visits: list[dict[str, Any]] = []
    for visit_dir in candidates:
        visit_path = visit_dir / "visit.json"
        if not visit_path.exists():
            continue
        try:
            visit = read_json(visit_path)
        except (OSError, json.JSONDecodeError):
            continue
        if visit.get("deleted"):
            continue
        visit_id = str(visit.get("id") or visit_dir.name)
        thought_path = visit_dir / "thought.md"
        thought = thought_path.read_text(encoding="utf-8", errors="replace") if thought_path.exists() else ""
        visit["id"] = visit_id
        visit["date"] = str(visit.get("date") or visit.get("visit_date") or "")[:10]
        visit["thought"] = thought or str(visit.get("thought") or visit.get("reflection") or "")
        visit["images"] = normalize_images(
            visit.get("images", []),
            lambda name, place_id=record_dir.name, current_visit_id=visit_id: (
                f"/api/modules/footprints/{place_id}/visits/{current_visit_id}/images/{name}"
            ),
        )
        visits.append(visit)
    visits.sort(key=lambda item: str(item.get("date") or item.get("updated_at") or ""), reverse=True)
    return visits


def footprint_visit_dir(place_id: str, visit_id: str) -> Path:
    base = (DATA_ROOT / "footprints" / place_id / "visits").resolve()
    target = (base / visit_id).resolve()
    if not str(target).startswith(str(base)):
        raise ValueError("invalid visit path")
    target.mkdir(parents=True, exist_ok=True)
    return target


def ensure_footprint_visit(place_id: str, visit_date: str) -> tuple[Path, dict[str, Any]]:
    place_dir = DATA_ROOT / "footprints" / place_id
    metadata_path = place_dir / "footprint.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"footprint not found: {place_id}")
    place_data = read_json(metadata_path)
    visits = read_footprint_visits(place_dir, place_data)
    for visit in visits:
        if str(visit.get("date") or "") == visit_date:
            visit_dir = footprint_visit_dir(place_id, str(visit["id"]))
            return visit_dir, read_json(visit_dir / "visit.json")
    visit_id = uuid.uuid4().hex
    visit_dir = footprint_visit_dir(place_id, visit_id)
    timestamp = now_iso()
    visit = {"id": visit_id, "date": visit_date, "images": [], "created_at": timestamp, "updated_at": timestamp}
    write_json(visit_dir / "visit.json", visit)
    visit_ids = list(place_data.get("visit_ids", [])) if isinstance(place_data.get("visit_ids"), list) else []
    if visit_id not in visit_ids:
        visit_ids.append(visit_id)
    place_data["visit_ids"] = visit_ids
    place_data["updated_at"] = timestamp
    write_json(metadata_path, place_data)
    return visit_dir, visit


def save_footprint_visit(place_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    visit_date = str(payload.get("date") or date.today().isoformat())[:10]
    visit_dir, visit = ensure_footprint_visit(place_id, visit_date)
    thought = str(payload.get("thought") or "")
    if thought:
        (visit_dir / "thought.md").write_text(thought, encoding="utf-8")
    visit["date"] = visit_date
    visit["updated_at"] = now_iso()
    write_json(visit_dir / "visit.json", visit)
    return record_from_directory(MODULE_BY_KEY["footprints"], DATA_ROOT / "footprints" / place_id) or {}


def footprint_visit_image_path(place_id: str, visit_id: str, image_name: str) -> Path:
    images_root = (DATA_ROOT / "footprints" / place_id / "visits" / visit_id / "images").resolve()
    candidate = (images_root / image_name).resolve()
    if not str(candidate).startswith(str(images_root)):
        raise ValueError("invalid image path")
    if not candidate.exists():
        raise FileNotFoundError(f"image not found: {image_name}")
    return candidate


def footprint_image_file(place_id: str, visit_id: str, image_name: str) -> Path | None:
    try:
        return footprint_visit_image_path(place_id, visit_id, image_name)
    except Exception:
        return None


def add_footprint_visit_images(place_id: str, visit_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    visit_dir = footprint_visit_dir(place_id, visit_id)
    visit_path = visit_dir / "visit.json"
    if not visit_path.exists():
        raise FileNotFoundError(f"visit not found: {visit_id}")
    images_dir = visit_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    visit = read_json(visit_path)
    images = list(visit.get("images", [])) if isinstance(visit.get("images"), list) else []
    files = payload.get("files")
    if not isinstance(files, list):
        raise ValueError("files must be a list")
    for item in files:
        if not isinstance(item, dict):
            continue
        raw_data = str(item.get("data") or "")
        if "," in raw_data and raw_data.startswith("data:"):
            raw_data = raw_data.split(",", 1)[1]
        file_name = unique_image_name(images_dir, str(item.get("name") or "image.png"))
        (images_dir / file_name).write_bytes(base64.b64decode(raw_data))
        images.append({"file_name": file_name, "label": str(item.get("label") or "")})
    visit["images"] = images
    visit["updated_at"] = now_iso()
    write_json(visit_path, visit)
    return record_from_directory(MODULE_BY_KEY["footprints"], DATA_ROOT / "footprints" / place_id) or {}


def update_footprint_visit_images(place_id: str, visit_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    visit_dir = footprint_visit_dir(place_id, visit_id)
    visit_path = visit_dir / "visit.json"
    if not visit_path.exists():
        raise FileNotFoundError(f"visit not found: {visit_id}")
    images_dir = visit_dir / "images"
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
        path = footprint_visit_image_path(place_id, visit_id, file_name)
        if path.exists() and file_name not in keep_names:
            next_images.append({"file_name": file_name, "label": label.strip()})
            keep_names.add(file_name)
    visit = read_json(visit_path)
    visit["images"] = next_images
    visit["updated_at"] = now_iso()
    write_json(visit_path, visit)
    for child in images_dir.iterdir():
        if child.is_file() and child.name not in keep_names:
            child.unlink(missing_ok=True)
    return record_from_directory(MODULE_BY_KEY["footprints"], DATA_ROOT / "footprints" / place_id) or {}


def classify_entry_images_to_footprint(entry_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    place_id = str(payload.get("footprint_id") or "")
    visit_date = str(payload.get("date") or date.today().isoformat())[:10]
    selected_names = payload.get("images")
    if not place_id:
        raise ValueError("footprint_id is required")
    if not isinstance(selected_names, list) or not selected_names:
        raise ValueError("images must be a non-empty list")
    entry_dir = DATA_ROOT / "entries" / entry_id
    entry_data = read_json(entry_dir / "entry.json")
    entry_images = normalize_images(entry_data.get("images", []))
    label_by_name = {image["file_name"]: image.get("label", "") for image in entry_images}
    visit_dir, visit = ensure_footprint_visit(place_id, visit_date)
    images_dir = visit_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    images = list(visit.get("images", [])) if isinstance(visit.get("images"), list) else []
    copied = 0
    for image_name in selected_names:
        source = entry_image_path(entry_id, str(image_name))
        file_name = unique_image_name(images_dir, source.name)
        shutil.copy2(source, images_dir / file_name)
        images.append({"file_name": file_name, "label": label_by_name.get(source.name, "")})
        copied += 1
    visit["images"] = images
    visit["updated_at"] = now_iso()
    write_json(visit_dir / "visit.json", visit)
    return {"ok": True, "copied": copied, "footprint": record_from_directory(MODULE_BY_KEY["footprints"], DATA_ROOT / "footprints" / place_id)}


def promote_light_plan_to_action(plan_id: str) -> dict[str, Any]:
    source_dir = DATA_ROOT / "plans" / plan_id
    source_path = source_dir / "plan.json"
    if not source_path.exists():
        raise FileNotFoundError(f"plan not found: {plan_id}")
    source = read_json(source_path)
    body = read_body(source_dir, source, MODULE_BY_KEY["plans"])
    record_id = uuid.uuid4().hex
    record_dir = DATA_ROOT / "action_plans" / record_id
    timestamp = now_iso()
    plan_date = str(source.get("due_date") or source.get("start_date") or date.today().isoformat())[:10]
    data = {
        "id": record_id,
        "title": str(source.get("title") or "未命名行动计划"),
        "plan_type": "日程型行动计划",
        "description": body,
        "start_date": plan_date,
        "end_date": "",
        "status": "进行中",
        "source_light_plan_id": plan_id,
        "tasks": [],
        "summary": "",
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    record_dir.mkdir(parents=True, exist_ok=True)
    write_json(record_dir / "action_plan.json", data)
    return record_from_directory(MODULE_BY_KEY["action_plans"], record_dir) or {}


def save_resource(payload: dict[str, Any]) -> dict[str, Any]:
    record_id = str(payload.get("id") or uuid.uuid4().hex)
    record_dir = DATA_ROOT / "resources" / record_id
    record_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = record_dir / "resource.json"
    existing = read_json(metadata_path) if metadata_path.exists() else {}
    extra = payload.get("extra") if isinstance(payload.get("extra"), dict) else {}
    timestamp = now_iso()
    data = {
        **existing, **extra,
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
        **existing, **extra,
        "id": record_id,
        "created_at": existing.get("created_at") or extra.get("created_at") or timestamp,
        "updated_at": timestamp,
    }
    title_field = module.title_fields[0]
    data[title_field] = str(payload.get("title") or data.get(title_field) or "")
    date_value = str(payload.get("date") or "")
    if date_value:
        data[module.date_fields[0]] = date_value
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
