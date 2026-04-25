from __future__ import annotations

import json
import shutil
import sys
import unittest
import zipfile
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from life_dairy.exchange import ExchangePackageExporter
from life_dairy.storage import DiaryStorage


class ExchangePackageExporterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case_dir = ROOT / ".tmp_testdata" / f"exchange_case_{uuid4().hex}"
        self.case_dir.mkdir(parents=True, exist_ok=False)

    def tearDown(self) -> None:
        shutil.rmtree(self.case_dir, ignore_errors=True)

    def test_exports_diary_directory_as_zip_with_manifest(self) -> None:
        storage = DiaryStorage(self.case_dir)
        entry = storage.create_empty_entry()
        entry.title = "交换包"
        saved = storage.save_entry(entry)

        zip_path = ExchangePackageExporter(self.case_dir).export_module("diary", self.case_dir / "exports")

        self.assertTrue(zip_path.exists())
        with zipfile.ZipFile(zip_path) as archive:
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            names = archive.namelist()

        self.assertEqual("diary", manifest["module"])
        self.assertIn(f"entries/{saved.id}/entry.json", names)
        self.assertIn(f"entries/{saved.id}/content.md", names)


if __name__ == "__main__":
    unittest.main()
