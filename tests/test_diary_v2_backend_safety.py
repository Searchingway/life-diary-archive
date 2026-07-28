from __future__ import annotations

import io
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "diary_v2.0"
if str(V2) not in sys.path:
    sys.path.insert(0, str(V2))

import data_api
import server


class DiaryV2BackendSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.original_data_root = data_api.DATA_ROOT
        data_api.DATA_ROOT = self.root / "Diary"

    def tearDown(self) -> None:
        data_api.DATA_ROOT = self.original_data_root
        self.temp_dir.cleanup()

    def test_safe_export_name_filters_windows_invalid_characters(self) -> None:
        result = data_api.safe_export_name('日记<测试>:"/\\|?*')
        for character in '<>:"/\\|?*':
            self.assertNotIn(character, result)
        self.assertTrue(result)

    def test_unique_output_path_does_not_overwrite_existing_file(self) -> None:
        target = self.root / "export.docx"
        target.write_text("existing", encoding="utf-8")
        unique = data_api.unique_output_path(target)
        self.assertEqual(unique.name, "export_1.docx")
        self.assertFalse(unique.exists())

    def test_ensure_child_path_accepts_child_and_rejects_escape(self) -> None:
        base = self.root / "base"
        self.assertEqual(data_api.ensure_child_path(base, "child"), (base / "child").resolve())
        with self.assertRaises(ValueError):
            data_api.ensure_child_path(base, "..", "outside")

    def test_atomic_write_json_produces_readable_json(self) -> None:
        target = self.root / "records" / "entry.json"
        data_api.atomic_write_json(target, {"title": "测试", "count": 1})
        self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"title": "测试", "count": 1})
        self.assertFalse(target.with_name("entry.json.tmp").exists())

    def test_atomic_write_text_concurrent_writes_leave_one_complete_value_and_no_temp_files(self) -> None:
        target = self.root / "records" / "entry.json"
        values = [f"保存内容-{index}-" + ("x" * 4096) for index in range(12)]
        barrier = threading.Barrier(len(values))
        errors: list[BaseException] = []

        def write(value: str) -> None:
            try:
                barrier.wait(timeout=5)
                data_api.atomic_write_text(target, value)
            except BaseException as error:
                errors.append(error)

        threads = [threading.Thread(target=write, args=(value,)) for value in values]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)

        self.assertFalse(errors)
        self.assertIn(target.read_text(encoding="utf-8"), values)
        self.assertEqual([], list(target.parent.glob(".entry.json.*.tmp")))

    def test_concurrent_entry_saves_leave_metadata_and_body_from_one_request(self) -> None:
        entry_id = "concurrent_entry"
        payloads = [
            {"id": entry_id, "title": "请求 A", "date": "2026-07-01", "body": "A 的完整正文"},
            {"id": entry_id, "title": "请求 B", "date": "2026-07-02", "body": "B 的完整正文"},
        ]
        barrier = threading.Barrier(len(payloads))
        errors: list[BaseException] = []

        def save(payload: dict[str, str]) -> None:
            try:
                barrier.wait(timeout=5)
                data_api.save_entry(payload)
            except BaseException as error:
                errors.append(error)

        threads = [threading.Thread(target=save, args=(payload,)) for payload in payloads]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)

        self.assertFalse(errors)
        record_dir = data_api.DATA_ROOT / "entries" / entry_id
        metadata = json.loads((record_dir / "entry.json").read_text(encoding="utf-8"))
        body = (record_dir / metadata["body_file"]).read_text(encoding="utf-8")
        self.assertIn(
            (metadata["title"], metadata["date"], body),
            {(payload["title"], payload["date"], payload["body"]) for payload in payloads},
        )

    def test_entry_save_uses_versioned_body_file_and_keeps_legacy_content_readable(self) -> None:
        entry_id = "legacy_entry"
        record_dir = data_api.DATA_ROOT / "entries" / entry_id
        record_dir.mkdir(parents=True)
        (record_dir / "content.md").write_text("旧正文", encoding="utf-8")
        data_api.atomic_write_json(
            record_dir / "entry.json",
            {
                "id": entry_id,
                "title": "旧标题",
                "date": "2026-07-01",
                "created_at": "2026-07-01T00:00:00+08:00",
                "updated_at": "2026-07-01T00:00:00+08:00",
                "body_file": "content.md",
            },
        )

        self.assertEqual("旧正文", data_api.record_from_directory(data_api.MODULE_BY_KEY["entries"], record_dir)["body"])

        saved = data_api.save_entry(
            {"id": entry_id, "title": "新标题", "date": "2026-07-02", "body": "新正文"},
        )

        metadata = json.loads((record_dir / "entry.json").read_text(encoding="utf-8"))
        self.assertRegex(metadata["body_file"], r"^content\.[A-Za-z0-9_-]+\.md$")
        self.assertEqual("新正文", (record_dir / metadata["body_file"]).read_text(encoding="utf-8"))
        self.assertEqual("新正文", saved["body"])
        self.assertFalse((record_dir / "content.md").exists())

    def test_failed_entry_metadata_write_keeps_previous_metadata_and_body(self) -> None:
        entry_id = "metadata_failure"
        first = data_api.save_entry(
            {"id": entry_id, "title": "已保存", "date": "2026-07-01", "body": "旧正文"},
        )
        record_dir = data_api.DATA_ROOT / "entries" / entry_id
        metadata_path = record_dir / "entry.json"
        original_write_json = data_api.write_json

        def fail_metadata_write(path: Path, data: dict[str, object]) -> None:
            if path == metadata_path:
                raise OSError("metadata write failed")
            original_write_json(path, data)

        with patch.object(data_api, "write_json", side_effect=fail_metadata_write):
            with self.assertRaisesRegex(OSError, "metadata write failed"):
                data_api.save_entry(
                    {"id": entry_id, "title": "未保存", "date": "2026-07-02", "body": "新正文"},
                )

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        self.assertEqual(first["title"], metadata["title"])
        self.assertEqual(first["body"], (record_dir / metadata["body_file"]).read_text(encoding="utf-8"))

    def test_validate_safe_id_accepts_safe_values(self) -> None:
        self.assertEqual(data_api.validate_safe_id("a" * 32), "a" * 32)
        self.assertEqual(data_api.validate_safe_id("place_2026-01"), "place_2026-01")

    def test_validate_safe_id_rejects_unsafe_values(self) -> None:
        for value in ("", "../abc", "a/b", "a\\b", "C:xxx", "a" * 81):
            with self.subTest(value=value), self.assertRaises(ValueError):
                data_api.validate_safe_id(value)

    def test_safe_file_name_uses_basename_and_rejects_invalid_name(self) -> None:
        self.assertEqual(data_api.safe_file_name("test.png"), "test.png")
        self.assertEqual(data_api.safe_file_name("../test.png"), "test.png")
        with self.assertRaises(ValueError):
            data_api.safe_file_name("bad:name.png")

    def test_entry_image_path_rejects_unsafe_image_name(self) -> None:
        with self.assertRaises(ValueError):
            data_api.entry_image_path("entry_1", "../secret.png")

    def test_decode_image_data_rejects_invalid_base64(self) -> None:
        with self.assertRaisesRegex(ValueError, "图片数据无效"):
            data_api.decode_image_data("not-valid-base64!")

    def test_decode_image_data_checks_encoded_size_before_decode(self) -> None:
        original_limit = data_api.MAX_IMAGE_BASE64_CHARS
        data_api.MAX_IMAGE_BASE64_CHARS = 4
        try:
            with self.assertRaisesRegex(ValueError, "图片过大"):
                data_api.decode_image_data("AAAAAA")
        finally:
            data_api.MAX_IMAGE_BASE64_CHARS = original_limit

    def test_server_rejects_oversized_request_before_reading_body(self) -> None:
        fake_handler = type(
            "FakeHandler",
            (),
            {
                "headers": {"Content-Length": str(server.MAX_REQUEST_BYTES + 1)},
                "rfile": io.BytesIO(b""),
            },
        )()
        with self.assertRaisesRegex(ValueError, "请求体过大"):
            server.LifeDiaryHandler.read_json_body(fake_handler)


if __name__ == "__main__":
    unittest.main()
