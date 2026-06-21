from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


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
