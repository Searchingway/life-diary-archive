from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path
from uuid import uuid4

from PySide6.QtWidgets import QApplication


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from life_dairy.footprint_storage import FootprintStorage
from life_dairy.main_window import DiaryMainWindow
from life_dairy.book_storage import BookStorage
from life_dairy.models import BookRelatedDiary
from life_dairy.storage import DiaryStorage


class DiaryMainWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.case_dir = ROOT / ".tmp_testdata" / f"window_case_{uuid4().hex}"
        self.case_dir.mkdir(parents=True, exist_ok=False)
        self.diary_storage = DiaryStorage(self.case_dir)
        self.footprint_storage = FootprintStorage(self.case_dir)
        self.book_storage = BookStorage(self.case_dir)
        self.window = DiaryMainWindow(self.diary_storage, self.footprint_storage, self.book_storage)

    def tearDown(self) -> None:
        self.window.close()
        shutil.rmtree(self.case_dir, ignore_errors=True)

    def test_main_window_has_diary_and_footprint_tabs(self) -> None:
        self.assertEqual(3, self.window.tabs.count())
        self.assertEqual("日记", self.window.tabs.tabText(0))
        self.assertEqual("足迹", self.window.tabs.tabText(1))
        self.assertEqual("读书", self.window.tabs.tabText(2))

    def test_cross_navigation_switches_between_diary_and_footprint(self) -> None:
        diary = self.diary_storage.create_empty_entry()
        diary.date = "2026-04-24"
        diary.title = "南湖"
        saved_diary = self.diary_storage.save_entry(diary)

        place = self.footprint_storage.create_empty_place()
        place.place_name = "南湖公园"
        visit = self.footprint_storage.create_empty_visit("2026-04-24")
        place.visits.append(visit)
        saved_place = self.footprint_storage.save_place(place)

        self.window.diary_page.refresh_list(select_id=saved_diary.id)
        self.window.diary_page._open_entry_by_id(saved_diary.id)
        self.window._open_footprints_for_date("2026-04-24")

        self.assertIs(self.window.tabs.currentWidget(), self.window.footprint_page)
        self.assertEqual(saved_place.id, self.window.footprint_page.current_place.id)
        self.assertEqual("2026-04-24", self.window.footprint_page._current_visit().date)

        self.window._open_diary_for_date("2026-04-24")

        self.assertIs(self.window.tabs.currentWidget(), self.window.diary_page)
        self.assertEqual(saved_diary.id, self.window.diary_page.current_entry.id)

    def test_place_list_shows_place_as_primary_and_visit_count_as_secondary(self) -> None:
        place = self.footprint_storage.create_empty_place()
        place.place_name = "青秀山"
        place.visits.append(self.footprint_storage.create_empty_visit("2026-04-24"))
        place.visits.append(self.footprint_storage.create_empty_visit("2026-04-25"))
        saved_place = self.footprint_storage.save_place(place)

        self.window.footprint_page.refresh_place_list(select_id=saved_place.id)
        item = self.window.footprint_page.place_list.item(0)

        self.assertIsNotNone(item)
        self.assertEqual("青秀山\n已关联 2 个日期", item.text())

    def test_visit_list_shows_date_and_daily_summary(self) -> None:
        place = self.footprint_storage.create_empty_place()
        place.place_name = "松花江畔"
        visit = self.footprint_storage.create_empty_visit("2026-04-18")
        visit.thought = "一个很喜欢的地方"
        place.visits.append(visit)
        saved_place = self.footprint_storage.save_place(place)

        self.window.footprint_page.refresh_place_list(select_id=saved_place.id)
        self.window.footprint_page._open_place_by_id(saved_place.id, select_visit_id=saved_place.visits[0].id)
        item = self.window.footprint_page.visit_list.item(0)

        self.assertIsNotNone(item)
        self.assertEqual("2026-04-18\n一个很喜欢的地方", item.text())

    def test_book_page_can_open_related_diary(self) -> None:
        diary = self.diary_storage.create_empty_entry()
        diary.date = "2026-04-24"
        diary.title = "读书夜"
        saved_diary = self.diary_storage.save_entry(diary)

        book = self.book_storage.create_empty_book()
        book.title = "人类简史"
        book.related_diaries.append(
            BookRelatedDiary(
                entry_id=saved_diary.id,
                date=saved_diary.date,
                title=saved_diary.display_title,
            ),
        )
        saved_book = self.book_storage.save_book(book)

        self.window.book_page.refresh_book_list(select_id=saved_book.id)
        self.window.book_page._open_book_by_id(saved_book.id)
        self.window.book_page.related_list.setCurrentRow(0)
        relation = self.window.book_page._current_related_diary()

        self.window._open_diary_from_book(relation.entry_id, relation.date)

        self.assertIs(self.window.tabs.currentWidget(), self.window.diary_page)
        self.assertEqual(saved_diary.id, self.window.diary_page.current_entry.id)


if __name__ == "__main__":
    unittest.main()
