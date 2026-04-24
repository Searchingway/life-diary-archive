from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

from docx import Document
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from life_dairy.exporters import DiaryExportItem, DiaryExporter
from life_dairy.models import DiaryImageDraft
from life_dairy.storage import DiaryStorage


class DiaryExporterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.case_dir = ROOT / ".tmp_testdata" / f"export_case_{uuid4().hex}"
        self.case_dir.mkdir(parents=True, exist_ok=False)
        self.storage = DiaryStorage(self.case_dir)
        self.export_dir = self.case_dir / "exports"
        self.exporter = DiaryExporter(self.export_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.case_dir, ignore_errors=True)

    def test_export_word_and_pdf_creates_files_and_uses_image_labels(self) -> None:
        image_path_one = self.case_dir / "cover.png"
        image_path_two = self.case_dir / "street.png"

        first = QImage(40, 40, QImage.Format.Format_ARGB32)
        first.fill(0xFF336699)
        second = QImage(50, 50, QImage.Format.Format_ARGB32)
        second.fill(0xFF996633)

        self.assertTrue(first.save(str(image_path_one)))
        self.assertTrue(second.save(str(image_path_two)))

        first_entry = self.storage.create_empty_entry()
        first_entry.date = "2026-04-22"
        first_entry.title = "第一篇"
        first_entry.body = "第一段\n第二段"
        first_saved = self.storage.save_entry(
            first_entry,
            [
                DiaryImageDraft(source_path=image_path_one, label="封面图"),
                DiaryImageDraft(source_path=image_path_two, label=""),
            ],
        )

        second_entry = self.storage.create_empty_entry()
        second_entry.date = "2026-04-24"
        second_entry.title = "第二篇"
        second_entry.body = "第三段"
        second_saved = self.storage.save_entry(second_entry)

        export_items = [
            DiaryExportItem(
                entry=first_saved,
                image_lookup={
                    image.file_name: self.storage.resolve_image_path(first_saved.id, image.file_name)
                    for image in first_saved.images
                },
            ),
            DiaryExportItem(
                entry=second_saved,
                image_lookup={},
            ),
        ]

        docx_path, pdf_path = self.exporter.export_entries_word_and_pdf(export_items)

        self.assertTrue(docx_path.exists())
        self.assertTrue(pdf_path.exists())
        self.assertGreater(docx_path.stat().st_size, 0)
        self.assertGreater(pdf_path.stat().st_size, 0)

        document = Document(docx_path)
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        self.assertIn("日期：", text)
        self.assertNotIn("创建时间：", text)
        self.assertNotIn("更新时间：", text)
        self.assertIn("封面图", text)
        self.assertLess(text.find("第一篇"), text.find("第二篇"))
        self.assertNotIn("cover.png", text)
        self.assertNotIn("street.png", text)

        with ZipFile(docx_path) as docx_zip:
            xml = docx_zip.read("word/document.xml").decode("utf-8")
        self.assertIn('w:type="page"', xml)


if __name__ == "__main__":
    unittest.main()
