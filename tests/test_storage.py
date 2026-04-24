from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from life_dairy.models import DiaryImageDraft
from life_dairy.storage import DiaryStorage


class DiaryStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case_dir = ROOT / ".tmp_testdata" / f"case_{uuid4().hex}"
        self.case_dir.mkdir(parents=True, exist_ok=False)
        self.storage = DiaryStorage(self.case_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.case_dir, ignore_errors=True)

    def test_save_and_reload_entry(self) -> None:
        entry = self.storage.create_empty_entry()
        entry.title = "第一篇"
        entry.body = "今天把项目第一步做起来。"

        saved = self.storage.save_entry(entry)
        loaded = self.storage.load_entry(saved.id)

        self.assertEqual("第一篇", loaded.title)
        self.assertEqual("今天把项目第一步做起来。", loaded.body)

    def test_list_entries_returns_saved_items(self) -> None:
        first = self.storage.create_empty_entry()
        first.title = "A"
        first.body = "first body"
        self.storage.save_entry(first)

        second = self.storage.create_empty_entry()
        second.title = "B"
        second.body = "second body"
        self.storage.save_entry(second)

        items = self.storage.list_entries()
        self.assertEqual(2, len(items))

    def test_list_entries_can_search_title_body_date_and_image_label(self) -> None:
        first = self.storage.create_empty_entry()
        first.date = "2026-04-24"
        first.title = "晨跑"
        first.body = "今天去江边跑步。"
        image_source = self.case_dir / "cover.jpg"
        image_source.write_bytes(b"jpeg-data")
        self.storage.save_entry(
            first,
            [DiaryImageDraft(source_path=image_source, label="江边风景")],
        )

        second = self.storage.create_empty_entry()
        second.date = "2026-04-23"
        second.title = "读书"
        second.body = "晚上继续读《置身事内》。"
        self.storage.save_entry(second)

        self.assertEqual([first.id], [item.id for item in self.storage.list_entries("晨跑")])
        self.assertEqual([second.id], [item.id for item in self.storage.list_entries("置身事内")])
        self.assertEqual([first.id], [item.id for item in self.storage.list_entries("2026-04-24")])
        self.assertEqual([first.id], [item.id for item in self.storage.list_entries("江边风景")])

    def test_list_entries_in_date_range_returns_oldest_first(self) -> None:
        first = self.storage.create_empty_entry()
        first.date = "2026-04-22"
        first.title = "第一天"
        self.storage.save_entry(first)

        second = self.storage.create_empty_entry()
        second.date = "2026-04-24"
        second.title = "第三天"
        self.storage.save_entry(second)

        third = self.storage.create_empty_entry()
        third.date = "2026-04-23"
        third.title = "第二天"
        self.storage.save_entry(third)

        items = self.storage.list_entries_in_date_range("2026-04-22", "2026-04-24")
        self.assertEqual(
            ["2026-04-22", "2026-04-23", "2026-04-24"],
            [item.date for item in items],
        )

    def test_delete_entry_removes_directory(self) -> None:
        entry = self.storage.create_empty_entry()
        saved = self.storage.save_entry(entry)
        self.storage.delete_entry(saved.id)
        self.assertTrue(self.storage.entry_dir(saved.id).exists())
        self.assertEqual([], self.storage.list_entries())

    def test_save_and_reload_images_with_label(self) -> None:
        image_source_one = self.case_dir / "cover.jpg"
        image_source_two = self.case_dir / "street.png"
        image_source_one.write_bytes(b"jpeg-data")
        image_source_two.write_bytes(b"png-data")

        entry = self.storage.create_empty_entry()
        saved = self.storage.save_entry(
            entry,
            [
                DiaryImageDraft(source_path=image_source_one, label="封面"),
                DiaryImageDraft(source_path=image_source_two, label=""),
            ],
        )
        loaded = self.storage.load_entry(saved.id)

        self.assertEqual(2, len(loaded.images))
        self.assertEqual("封面", loaded.images[0].label)
        self.assertEqual("", loaded.images[1].label)
        self.assertTrue(self.storage.resolve_image_path(saved.id, loaded.images[0].file_name).exists())
        self.assertTrue(self.storage.resolve_image_path(saved.id, loaded.images[1].file_name).exists())

    def test_save_with_removed_image_updates_metadata(self) -> None:
        image_source_one = self.case_dir / "cover.jpg"
        image_source_two = self.case_dir / "street.png"
        image_source_one.write_bytes(b"jpeg-data")
        image_source_two.write_bytes(b"png-data")

        entry = self.storage.create_empty_entry()
        saved = self.storage.save_entry(
            entry,
            [
                DiaryImageDraft(source_path=image_source_one, label="封面"),
                DiaryImageDraft(source_path=image_source_two, label="街景"),
            ],
        )
        loaded = self.storage.load_entry(saved.id)

        kept_image = loaded.images[0]
        kept_path = self.storage.resolve_image_path(saved.id, kept_image.file_name)
        saved_again = self.storage.save_entry(
            loaded,
            [DiaryImageDraft(source_path=kept_path, label=kept_image.label)],
        )

        self.assertEqual([kept_path.name], [item.file_name for item in saved_again.images])
        self.assertEqual(["封面"], [item.label for item in saved_again.images])


if __name__ == "__main__":
    unittest.main()
