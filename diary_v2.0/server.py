from __future__ import annotations

import json
import mimetypes
import os
import re
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import data_api

from data_api import (
    APP_TITLE,
    FRONTEND_DIST,
    MODULE_BY_KEY,
    add_entry_images,
    add_footprint_visit_images,
    build_overview,
    classify_entry_images_to_footprint,
    configured_export_dir,
    data_root_status,
    delete_generic_record,
    ensure_child_path,
    entry_image_path,
    footprint_visit_image_path,
    list_module_records,
    migrate_legacy_data_if_needed,
    migrate_current_data_root,
    promote_light_plan_to_action,
    read_settings,
    save_footprint_visit,
    save_generic_record,
    save_resource,
    select_and_store_export_directory,
    select_data_root_directory,
    update_entry_images,
    update_footprint_visit_images,
    unique_output_path,
    write_settings,
)
from export_service import (
    export_all_entries_txt,
    export_all_modules,
    export_all_entries_word_pdf,
    export_entry_word_pdf,
    export_footprints_word,
    export_module_txt,
    export_notes_markdown,
)
from sync_service import SyncService

MAX_REQUEST_BYTES = 30 * 1024 * 1024
sync_service = SyncService()


class LifeDiaryHandler(BaseHTTPRequestHandler):
    server_version = "LifeDiary2/1.0"

    def log_message(self, format: str, *args: object) -> None:
        pass

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/overview":
            self.send_json(build_overview())
            return
        if parsed.path == "/api/settings":
            self.send_json({**read_settings(), "export_dir": str(configured_export_dir())})
            return
        if parsed.path == "/api/data-root":
            self.send_json(data_root_status())
            return
        session_match = re.fullmatch(r"/api/sync/sessions/([^/]+)", parsed.path)
        if session_match:
            try:
                self.send_json(sync_service.get_session(unquote(session_match.group(1))))
            except Exception as exc:
                self.send_error(HTTPStatus.NOT_FOUND, str(exc))
            return
        image_match = re.fullmatch(r"/api/modules/entries/([^/]+)/images/(.+)", parsed.path)
        if image_match:
            try:
                path = entry_image_path(unquote(image_match.group(1)), unquote(image_match.group(2)))
                self.send_file(path)
            except Exception as exc:
                self.send_error(HTTPStatus.NOT_FOUND, str(exc))
            return
        footprint_image_match = re.fullmatch(r"/api/modules/footprints/([^/]+)/visits/([^/]+)/images/(.+)", parsed.path)
        if footprint_image_match:
            try:
                path = footprint_visit_image_path(
                    unquote(footprint_image_match.group(1)),
                    unquote(footprint_image_match.group(2)),
                    unquote(footprint_image_match.group(3)),
                )
                self.send_file(path)
            except Exception as exc:
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
        with data_api.data_mutation_lock():
            self._do_POST()

    def _do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/actions/open-data-root":
            data_api.DATA_ROOT.mkdir(parents=True, exist_ok=True)
            os.startfile(data_api.DATA_ROOT)  # type: ignore[attr-defined]
            self.send_json({"ok": True})
            return
        if parsed.path == "/api/actions/select-data-root":
            try:
                self.send_json({"selected_path": str(select_data_root_directory())})
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        if parsed.path == "/api/actions/migrate-data-root":
            try:
                payload = self.read_json_body()
                self.send_json(migrate_current_data_root(str(payload.get("destination") or "")))
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        if parsed.path == "/api/actions/select-export-dir":
            try:
                self.send_json(select_and_store_export_directory())
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        if parsed.path == "/api/sync/select-mobile-zip":
            try:
                self.send_json({"zip_path": sync_service.select_mobile_snapshot_zip()})
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        if parsed.path == "/api/sync/import-mobile":
            try:
                payload = self.read_json_body()
                self.send_json(sync_service.prepare_mobile_import(str(payload.get("zip_path") or "")))
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        resolve_entry_match = re.fullmatch(r"/api/sync/sessions/([^/]+)/resolve-entry", parsed.path)
        if resolve_entry_match:
            try:
                payload = self.read_json_body()
                self.send_json(sync_service.resolve_entry_conflict(unquote(resolve_entry_match.group(1)), str(payload.get("conflict_id") or ""), str(payload.get("body") or ""), payload.get("title")))
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        resolve_generic_match = re.fullmatch(r"/api/sync/sessions/([^/]+)/resolve-generic", parsed.path)
        if resolve_generic_match:
            try:
                payload = self.read_json_body()
                self.send_json(sync_service.resolve_generic_conflict(unquote(resolve_generic_match.group(1)), str(payload.get("conflict_id") or ""), str(payload.get("choice") or "")))
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        commit_match = re.fullmatch(r"/api/sync/sessions/([^/]+)/commit", parsed.path)
        if commit_match:
            try:
                self.send_json(sync_service.commit_import(unquote(commit_match.group(1))))
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        if parsed.path == "/api/sync/export-canonical":
            try:
                payload = self.read_json_body()
                requested = str(payload.get("output_path") or "").strip()
                output = Path(requested).expanduser().resolve() if requested else unique_output_path(configured_export_dir() / "LifeDiary-Desktop-Canonical.zip")
                self.send_json({"zip_path": sync_service.create_desktop_canonical_zip(output)})
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        if parsed.path == "/api/settings":
            try:
                self.send_json(write_settings(self.read_json_body()))
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        image_match = re.fullmatch(r"/api/modules/entries/([^/]+)/images", parsed.path)
        if image_match:
            try:
                self.send_json(add_entry_images(unquote(image_match.group(1)), self.read_json_body()))
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        classify_match = re.fullmatch(r"/api/modules/entries/([^/]+)/classify-images", parsed.path)
        if classify_match:
            try:
                self.send_json(classify_entry_images_to_footprint(unquote(classify_match.group(1)), self.read_json_body()))
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        footprint_image_match = re.fullmatch(r"/api/modules/footprints/([^/]+)/visits/([^/]+)/images", parsed.path)
        if footprint_image_match:
            try:
                self.send_json(
                    add_footprint_visit_images(
                        unquote(footprint_image_match.group(1)),
                        unquote(footprint_image_match.group(2)),
                        self.read_json_body(),
                    )
                )
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        visit_match = re.fullmatch(r"/api/modules/footprints/([^/]+)/visits", parsed.path)
        if visit_match:
            try:
                self.send_json(save_footprint_visit(unquote(visit_match.group(1)), self.read_json_body()))
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        promote_match = re.fullmatch(r"/api/modules/plans/([^/]+)/promote-action", parsed.path)
        if promote_match:
            try:
                self.send_json(promote_light_plan_to_action(unquote(promote_match.group(1))))
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        if parsed.path == "/api/modules/entries/export-all":
            try:
                self.send_json(export_all_entries_word_pdf(self.read_json_body()))
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        if parsed.path == "/api/modules/entries/export-txt":
            try:
                self.send_json(export_all_entries_txt(self.read_json_body()))
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        if parsed.path == "/api/export/all":
            try:
                self.send_json(export_all_modules(self.read_json_body()))
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        if parsed.path == "/api/modules/footprints/export-word":
            try:
                self.send_json(export_footprints_word(self.read_json_body()))
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        if parsed.path == "/api/modules/notes/export-md":
            try:
                self.send_json(export_notes_markdown(self.read_json_body()))
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        module_export_match = re.fullmatch(r"/api/modules/([^/]+)/export-txt", parsed.path)
        if module_export_match:
            try:
                self.send_json(export_module_txt(unquote(module_export_match.group(1)), self.read_json_body()))
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        export_match = re.fullmatch(r"/api/modules/entries/([^/]+)/export", parsed.path)
        if export_match:
            try:
                self.send_json(export_entry_word_pdf(unquote(export_match.group(1))))
            except Exception as exc:
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
        except Exception as exc:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def do_PUT(self) -> None:
        with data_api.data_mutation_lock():
            self._do_PUT()

    def _do_PUT(self) -> None:
        parsed = urlparse(self.path)
        image_match = re.fullmatch(r"/api/modules/entries/([^/]+)/images", parsed.path)
        if image_match:
            try:
                self.send_json(update_entry_images(unquote(image_match.group(1)), self.read_json_body()))
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        footprint_image_match = re.fullmatch(r"/api/modules/footprints/([^/]+)/visits/([^/]+)/images", parsed.path)
        if footprint_image_match:
            try:
                self.send_json(
                    update_footprint_visit_images(
                        unquote(footprint_image_match.group(1)),
                        unquote(footprint_image_match.group(2)),
                        self.read_json_body(),
                    )
                )
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        self.send_error(HTTPStatus.NOT_FOUND, "unknown endpoint")

    def do_DELETE(self) -> None:
        with data_api.data_mutation_lock():
            self._do_DELETE()

    def _do_DELETE(self) -> None:
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
        except Exception as exc:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def read_json_body(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("Content-Length 无效") from exc
        if length < 0:
            raise ValueError("Content-Length 无效")
        if length > MAX_REQUEST_BYTES:
            raise ValueError("请求体过大")
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
        relative = unquote(request_path).strip("/") or "index.html"
        try:
            target = ensure_child_path(FRONTEND_DIST, relative)
        except ValueError:
            target = ensure_child_path(FRONTEND_DIST, "index.html")
        if not target.exists() or target.is_dir():
            target = ensure_child_path(FRONTEND_DIST, "index.html")
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
