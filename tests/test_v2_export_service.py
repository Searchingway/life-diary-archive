from __future__ import annotations

import sys
import unittest
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

from docx import Document


DIARY_V2_ROOT = Path(__file__).resolve().parents[1] / "diary_v2.0"
if str(DIARY_V2_ROOT) not in sys.path:
    sys.path.insert(0, str(DIARY_V2_ROOT))

from export_service import append_footprint_record_to_docx
import export_service


class RawDataZipTests(unittest.TestCase):
    def test_nested_output_directory_is_excluded_without_excluding_similar_names(self) -> None:
        temporary_root = Path(__file__).resolve().parents[1] / ".tmp_testdata"
        temporary_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_root) as folder:
            root = Path(folder) / "Diary"
            target = root / "custom-backups"
            target.mkdir(parents=True)
            (target / "previous.zip").write_bytes(b"previous backup")
            (root / "entries").mkdir()
            (root / "entries" / "entry.json").write_text('{"title":"测试"}', encoding="utf-8")
            (root / "exports").mkdir()
            (root / "exports" / "old.txt").write_text("output", encoding="utf-8")
            (root / "exports-notes").mkdir()
            (root / "exports-notes" / "note.txt").write_text("keep", encoding="utf-8")
            with patch.object(export_service, "DATA_ROOT", root):
                result = export_service.zip_raw_data(target)
            with zipfile.ZipFile(result) as archive:
                self.assertEqual(set(archive.namelist()), {"entries/entry.json", "exports-notes/note.txt"})
                self.assertIsNone(archive.testzip())

    def test_zip_in_data_root_does_not_include_itself(self) -> None:
        temporary_root = Path(__file__).resolve().parents[1] / ".tmp_testdata"
        temporary_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_root) as folder:
            root = Path(folder)
            (root / "record.txt").write_text("keep", encoding="utf-8")
            with patch.object(export_service, "DATA_ROOT", root):
                result = export_service.zip_raw_data(root)
            with zipfile.ZipFile(result) as archive:
                self.assertEqual(archive.namelist(), ["record.txt"])


class FootprintWordExportTests(unittest.TestCase):
    def test_place_name_is_primary_heading_and_visit_date_is_secondary(self) -> None:
        document = Document()
        append_footprint_record_to_docx(
            document,
            {
                "id": "place-1",
                "title": "东北农业大学武术馆",
                "body": "地点描述",
                "extra": {
                    "visits": [
                        {
                            "id": "visit-1",
                            "date": "2026-06-12",
                            "thought": "访问记录",
                            "images": [],
                        }
                    ]
                },
            },
        )

        styles_by_text = {
            paragraph.text: paragraph.style.name
            for paragraph in document.paragraphs
            if paragraph.text
        }
        self.assertEqual(styles_by_text["东北农业大学武术馆"], "Heading 1")
        self.assertEqual(styles_by_text["2026-06-12"], "Heading 2")


if __name__ == "__main__":
    unittest.main()
