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

from life_dairy.book_storage import BookStorage
from life_dairy.exchange import ExchangePackageExporter, safe_filename
from life_dairy.footprint_storage import FootprintStorage
from life_dairy.plan_storage import PlanStorage
from life_dairy.storage import DiaryStorage


class ExchangePackageExporterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case_dir = ROOT / ".tmp_testdata" / f"exchange_case_{uuid4().hex}"
        self.case_dir.mkdir(parents=True, exist_ok=False)

    def tearDown(self) -> None:
        shutil.rmtree(self.case_dir, ignore_errors=True)

    def test_exports_diary_as_readable_zip_with_manifest_mapping(self) -> None:
        storage = DiaryStorage(self.case_dir)
        entry = storage.create_empty_entry()
        entry.date = "2026-04-29"
        entry.title = "武馆练拳和接单"
        entry.body = "今天复盘了接单节奏。"
        saved = storage.save_entry(entry)

        zip_path = ExchangePackageExporter(self.case_dir).export_module("diary", self.case_dir / "exports")

        with zipfile.ZipFile(zip_path) as archive:
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            names = archive.namelist()

        readable_dir = "entries/2026-04-29_武馆练拳和接单"
        self.assertEqual("diary", manifest["module"])
        self.assertEqual(1, manifest["record_count"])
        self.assertIn(f"{readable_dir}/entry.json", names)
        self.assertIn(f"{readable_dir}/content.md", names)
        self.assertEqual(
            {
                "module": "entries",
                "original_id": saved.id,
                "display_name": "2026-04-29_武馆练拳和接单",
                "relative_path": readable_dir,
                "date": "2026-04-29",
                "title": "武馆练拳和接单",
                "exported_at": manifest["exported_at"],
            },
            manifest["records"][0],
        )

    def test_diary_export_skips_deleted_and_blank_drafts(self) -> None:
        storage = DiaryStorage(self.case_dir)
        first = storage.create_empty_entry()
        first.date = "2026-04-29"
        first.title = "保留一"
        storage.save_entry(first)

        second = storage.create_empty_entry()
        second.date = "2026-04-30"
        second.title = "保留二"
        storage.save_entry(second)

        deleted = storage.create_empty_entry()
        deleted.date = "2026-05-01"
        deleted.title = "已删除"
        deleted_saved = storage.save_entry(deleted)
        storage.delete_entry(deleted_saved.id)

        blank = storage.create_empty_entry()
        blank.date = "2026-05-02"
        storage.save_entry(blank)

        zip_path = ExchangePackageExporter(self.case_dir).export_module("diary", self.case_dir / "exports")

        with zipfile.ZipFile(zip_path) as archive:
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            entry_jsons = [name for name in archive.namelist() if name.startswith("entries/") and name.endswith("/entry.json")]

        self.assertEqual(2, len(entry_jsons))
        self.assertEqual(2, manifest["record_count"])
        self.assertEqual({"保留一", "保留二"}, {record["title"] for record in manifest["records"]})

    def test_book_export_uses_book_title(self) -> None:
        storage = BookStorage(self.case_dir)
        book = storage.create_empty_book()
        book.title = "意识形态的崇高客体"
        book.author = "齐泽克"
        storage.save_book(book)

        zip_path = ExchangePackageExporter(self.case_dir).export_module("book", self.case_dir / "exports")

        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))

        self.assertIn("books/意识形态的崇高客体/book.json", names)
        self.assertEqual("意识形态的崇高客体", manifest["records"][0]["display_name"])

    def test_footprint_export_uses_place_name_and_visit_date(self) -> None:
        storage = FootprintStorage(self.case_dir)
        place = storage.create_empty_place()
        place.place_name = "主楼330"
        visit = storage.create_empty_visit("2026-04-29")
        visit.thought = "把这次讨论记下来。"
        place.visits = [visit]
        storage.save_place(place)

        zip_path = ExchangePackageExporter(self.case_dir).export_module("footprint", self.case_dir / "exports")

        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))

        self.assertIn("footprints/主楼330/footprint.json", names)
        self.assertIn("footprints/主楼330/visits/2026-04-29/visit.json", names)
        self.assertIn("footprints/主楼330/visits/2026-04-29/thought.md", names)
        self.assertEqual("主楼330", manifest["records"][0]["display_name"])

    def test_safe_filename_replaces_windows_invalid_characters(self) -> None:
        self.assertEqual("A_B_C_D_E_F_G_H_I", safe_filename(' A/B:C*D?E"F<G>H|I '))

        storage = DiaryStorage(self.case_dir)
        entry = storage.create_empty_entry()
        entry.date = "2026-04-29"
        entry.title = 'A/B:C*D?E"F<G>H|I'
        storage.save_entry(entry)

        zip_path = ExchangePackageExporter(self.case_dir).export_module("diary", self.case_dir / "exports")

        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()

        self.assertIn("entries/2026-04-29_A_B_C_D_E_F_G_H_I/entry.json", names)

    def test_duplicate_display_names_get_number_suffix(self) -> None:
        storage = DiaryStorage(self.case_dir)
        for _ in range(2):
            entry = storage.create_empty_entry()
            entry.date = "2026-04-29"
            entry.title = "同名记录"
            entry.body = "不是空白草稿。"
            storage.save_entry(entry)

        zip_path = ExchangePackageExporter(self.case_dir).export_module("diary", self.case_dir / "exports")

        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()

        self.assertIn("entries/2026-04-29_同名记录/entry.json", names)
        self.assertIn("entries/2026-04-29_同名记录_02/entry.json", names)

    def test_plan_export_is_filtered_and_uses_readable_name(self) -> None:
        storage = PlanStorage(self.case_dir)
        plan = storage.create_empty_plan()
        plan.due_date = "2026-05-01"
        plan.title = "今晚不刷短视频"
        plan.plan_type = "subtract"
        plan.avoid_behavior = "连续刷短视频超过30分钟"
        storage.save_plan(plan)

        zip_path = ExchangePackageExporter(self.case_dir).export_module("plan", self.case_dir / "exports")

        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))

        self.assertIn("plans/2026-05-01_今晚不刷短视频/plan.json", names)
        self.assertEqual("plans", manifest["records"][0]["module"])


if __name__ == "__main__":
    unittest.main()
