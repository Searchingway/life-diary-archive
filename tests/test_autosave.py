from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from PySide6.QtWidgets import QApplication, QMessageBox


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from life_dairy.book_storage import BookStorage
from life_dairy.footprint_storage import FootprintStorage
from life_dairy.lesson_storage import LessonStorage
from life_dairy.main_window import DiaryMainWindow
from life_dairy.models import DiaryImageDraft
from life_dairy.plan_storage import PlanStorage
from life_dairy.storage import DiaryStorage


class AutoSaveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.case_dir = ROOT / ".tmp_testdata" / f"autosave_case_{uuid4().hex}"
        self.case_dir.mkdir(parents=True, exist_ok=False)
        self.diary_storage = DiaryStorage(self.case_dir)
        self.footprint_storage = FootprintStorage(self.case_dir)
        self.book_storage = BookStorage(self.case_dir)
        self.plan_storage = PlanStorage(self.case_dir)
        self.lesson_storage = LessonStorage(self.case_dir)
        self.window = DiaryMainWindow(
            self.diary_storage,
            self.footprint_storage,
            self.book_storage,
            self.plan_storage,
            self.lesson_storage,
        )

    def tearDown(self) -> None:
        self.window.close()
        shutil.rmtree(self.case_dir, ignore_errors=True)

    def test_diary_changes_can_auto_save(self) -> None:
        page = self.window.diary_page
        page.title_input.setText("自动保存日记")
        page.body_edit.setPlainText("停止输入后自动落盘。")

        self.assertTrue(page.perform_auto_save())
        loaded = self.diary_storage.load_entry(page.current_entry.id)

        self.assertEqual("自动保存日记", loaded.title)
        self.assertEqual("停止输入后自动落盘。", loaded.body)
        self.assertFalse(page.has_unsaved_changes())

    def test_plan_changes_can_auto_save_and_manual_save_still_works(self) -> None:
        page = self.window.plan_page
        page.title_input.setText("自动保存轻计划")
        page.notes_edit.setPlainText("先写一个轻量计划。")

        self.assertTrue(page.perform_auto_save())
        loaded = self.plan_storage.load_plan(page.current_plan.id)
        self.assertEqual("自动保存轻计划", loaded.title)

        page.notes_edit.setPlainText("手动保存仍然可用。")
        self.assertTrue(page.save_plan())
        loaded_again = self.plan_storage.load_plan(page.current_plan.id)
        self.assertEqual("手动保存仍然可用。", loaded_again.notes)

    def test_lesson_changes_can_auto_save(self) -> None:
        page = self.window.lesson_page
        page.title_input.setText("自动保存反思")
        page.event_edit.setPlainText("这次没有忘记保存。")
        page.next_action_edit.setPlainText("以后依赖自动保存兜底。")

        self.assertTrue(page.perform_auto_save())
        loaded = self.lesson_storage.load_lesson(page.current_lesson.id)

        self.assertEqual("自动保存反思", loaded.title)
        self.assertEqual("这次没有忘记保存。", loaded.event)
        self.assertEqual("以后依赖自动保存兜底。", loaded.next_action)

    def test_reload_saved_content_does_not_get_auto_saved_back_over_it(self) -> None:
        page = self.window.diary_page
        page.title_input.setText("恢复测试")
        page.body_edit.setPlainText("已保存内容")
        self.assertTrue(page.save_entry())

        page.body_edit.setPlainText("未保存改动")
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            page.reload_current_entry()

        self.assertFalse(page.has_unsaved_changes())
        self.assertTrue(page.perform_auto_save())
        loaded = self.diary_storage.load_entry(page.current_entry.id)
        self.assertEqual("已保存内容", loaded.body)

    def test_switching_tabs_auto_saves_pending_page(self) -> None:
        page = self.window.diary_page
        self.window.tabs.setCurrentWidget(page)
        page.title_input.setText("切换页签保存")
        page.body_edit.setPlainText("切换到轻计划前保存。")

        self.window.tabs.setCurrentWidget(self.window.plan_page)
        loaded = self.diary_storage.load_entry(page.current_entry.id)

        self.assertEqual("切换页签保存", loaded.title)
        self.assertEqual("切换到轻计划前保存。", loaded.body)

    def test_image_label_change_can_auto_save(self) -> None:
        image_source = self.case_dir / "photo.jpg"
        image_source.write_bytes(b"jpeg-data")
        entry = self.diary_storage.create_empty_entry()
        saved = self.diary_storage.save_entry(
            entry,
            [DiaryImageDraft(source_path=image_source, label="旧备注")],
        )

        page = self.window.diary_page
        page._open_entry_by_id(saved.id)
        page.image_list.setCurrentRow(0)
        page.image_label_input.setText("新备注")

        self.assertTrue(page.perform_auto_save())
        loaded = self.diary_storage.load_entry(saved.id)
        self.assertEqual("新备注", loaded.images[0].label)

    def test_blank_new_plan_is_not_auto_saved(self) -> None:
        page = self.window.plan_page
        page.new_plan()
        page._mark_dirty()

        self.assertTrue(page.perform_auto_save())
        self.assertFalse(self.plan_storage.plan_dir(page.current_plan.id).exists())


if __name__ == "__main__":
    unittest.main()
