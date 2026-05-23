from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path
from uuid import uuid4

from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QMessageBox


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from life_dairy.note_page import NotePage
from life_dairy.note_storage import NoteStorage


class NotePageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.case_dir = ROOT / ".tmp_testdata" / f"note_page_case_{uuid4().hex}"
        self.case_dir.mkdir(parents=True, exist_ok=False)
        self.storage = NoteStorage(self.case_dir)
        self.page = NotePage(self.storage)

    def tearDown(self) -> None:
        self.page.deleteLater()
        shutil.rmtree(self.case_dir, ignore_errors=True)

    def test_new_note_creates_empty_form(self) -> None:
        self.page.new_note()
        self.assertEqual("", self.page.title_input.text())
        self.assertEqual("", self.page.description_edit.toPlainText())
        self.assertEqual("", self.page.body_edit.toPlainText())
        self.assertIsNotNone(self.page.current_note)
        self.assertTrue(self.page.current_note.id)

    def test_fill_form_populates_ui(self) -> None:
        note = self.storage.create_empty_note()
        note.title = "测试标题"
        note.description = "测试描述"
        note.body = "测试正文"
        self.page._fill_form(note)
        self.assertEqual("测试标题", self.page.title_input.text())
        self.assertEqual("测试描述", self.page.description_edit.toPlainText())
        self.assertEqual("测试正文", self.page.body_edit.toPlainText())

    def test_read_form_reads_from_ui(self) -> None:
        self.page.new_note()
        self.page.title_input.setText("标题")
        self.page.description_edit.setPlainText("描述")
        self.page.body_edit.setPlainText("正文")
        note = self.page._read_form()
        self.assertEqual("标题", note.title)
        self.assertEqual("描述", note.description)
        self.assertEqual("正文", note.body)

    def test_save_note_persists_and_refreshes_list(self) -> None:
        self.page.new_note()
        self.page.title_input.setText("保存测试")
        self.page.description_edit.setPlainText("保存描述")
        self.page.body_edit.setPlainText("保存正文")
        self.assertTrue(self.page.save_note())
        self.assertEqual(1, self.page.note_list.count())
        # list shows display_title
        self.assertIn("保存测试", self.page.note_list.item(0).text())

    def test_delete_current_note_removes_from_list(self) -> None:
        self.page.new_note()
        self.page.title_input.setText("将被删除")
        self.page.save_note()
        self.assertEqual(1, self.page.note_list.count())
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            self.page.delete_current_note()
        self.assertEqual(0, len(self.storage.list_notes()))

    def test_dirty_state_tracking(self) -> None:
        self.page.new_note()
        self.assertFalse(self.page.has_unsaved_changes())
        self.page.title_input.setText("修改")
        self.assertTrue(self.page.has_unsaved_changes())
        self.page.save_note()
        self.assertFalse(self.page.has_unsaved_changes())

    def test_dirty_state_tracks_description_change(self) -> None:
        self.page.new_note()
        self.assertFalse(self.page.has_unsaved_changes())
        self.page.description_edit.setPlainText("描述修改")
        self.assertTrue(self.page.has_unsaved_changes())

    def test_dirty_state_tracks_body_change(self) -> None:
        self.page.new_note()
        self.assertFalse(self.page.has_unsaved_changes())
        self.page.body_edit.setPlainText("正文修改")
        self.assertTrue(self.page.has_unsaved_changes())

    def test_auto_save_persists_content(self) -> None:
        self.page.new_note()
        self.page.title_input.setText("自动保存")
        self.page.description_edit.setPlainText("自动描述")
        self.page.body_edit.setPlainText("自动正文")
        self.assertTrue(self.page.perform_auto_save())
        self.assertFalse(self.page.has_unsaved_changes())
        loaded = self.storage.load_note(self.page.current_note.id)
        self.assertEqual("自动保存", loaded.title)
        self.assertEqual("自动描述", loaded.description)
        self.assertEqual("自动正文", loaded.body)

    def test_auto_save_blank_note_does_not_persist(self) -> None:
        self.page.new_note()
        self.page._mark_dirty()
        self.assertTrue(self.page.perform_auto_save())
        self.assertFalse(self.storage.note_dir(self.page.current_note.id).exists())

    def test_search_filters_note_list(self) -> None:
        self.page.new_note()
        self.page.title_input.setText("Python 笔记")
        self.page.save_note()
        self.page.new_note()
        self.page.title_input.setText("Java 笔记")
        self.page.save_note()
        self.assertEqual(2, self.page.note_list.count())
        self.page.search_input.setText("Python")
        self.page.refresh_note_list()
        self.assertEqual(1, self.page.note_list.count())

    def test_open_note_by_id_loads_correct_note(self) -> None:
        note = self.storage.create_empty_note()
        note.title = "通过ID打开"
        note.body = "正文内容"
        saved = self.storage.save_note(note)
        self.page.open_note_by_id(saved.id)
        self.assertEqual("通过ID打开", self.page.title_input.text())
        self.assertEqual("正文内容", self.page.body_edit.toPlainText())

    def test_reload_current_note_restores_saved_content(self) -> None:
        self.page.new_note()
        self.page.title_input.setText("原始标题")
        self.page.body_edit.setPlainText("原始正文")
        self.page.save_note()
        self.page.title_input.setText("未保存修改")
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            self.page.reload_current_note()
        self.assertEqual("原始标题", self.page.title_input.text())
        self.assertEqual("原始正文", self.page.body_edit.toPlainText())

    def test_list_text_shows_title_and_description_preview(self) -> None:
        self.page.new_note()
        self.page.title_input.setText("列表标题")
        self.page.description_edit.setPlainText("列表描述")
        self.page.save_note()
        text = self.page.note_list.item(0).text()
        self.assertIn("列表标题", text)
        self.assertIn("列表描述", text)

    def test_dirty_state_changed_signal_emitted(self) -> None:
        emitted = []

        def on_dirty(val: bool) -> None:
            emitted.append(val)

        self.page.dirty_state_changed.connect(on_dirty)
        self.page.new_note()
        self.page.title_input.setText("触发信号")
        self.assertTrue(True in emitted)


if __name__ == "__main__":
    unittest.main()
