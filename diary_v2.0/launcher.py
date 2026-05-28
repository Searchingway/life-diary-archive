from __future__ import annotations

import json
import mimetypes
import os
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

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView


APP_TITLE = "人生档案 Diary Desktop 2.0"
BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
FRONTEND_DIST = BASE_DIR / "Untitled" / "dist"
DATA_ROOT = Path(os.environ.get("LIFE_DIARY_DATA_ROOT", REPO_ROOT / "data" / "Diary")).resolve()


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
    return {"data_root": str(DATA_ROOT), "modules": modules, "recent": recent[:20]}


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


class LifeDiaryHandler(BaseHTTPRequestHandler):
    server_version = "LifeDiary2/1.0"

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/overview":
            self.send_json(build_overview())
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
        if not parsed.path.startswith("/api/modules/"):
            self.send_error(HTTPStatus.NOT_FOUND, "unknown endpoint")
            return
        module_key = unquote(parsed.path.removeprefix("/api/modules/"))
        try:
            payload = self.read_json_body()
            if module_key == "entries":
                self.send_json(save_entry(payload))
            elif module_key == "resources":
                self.send_json(save_resource(payload))
            else:
                self.send_error(HTTPStatus.BAD_REQUEST, "this module is read-only in 2.0 preview")
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
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
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
