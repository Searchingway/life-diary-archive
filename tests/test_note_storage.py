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

from life_dairy.note_storage import NoteEntry, NoteStorage


class NoteStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case_dir = ROOT / ".tmp_testdata" / f"note_case_{uuid4().hex}"
        self.case_dir.mkdir(parents=True, exist_ok=False)

    def tearDown(self) -> None:
        shutil.rmtree(self.case_dir, ignore_errors=True)

    def test_note_entry_to_dict_roundtrip(self) -> None:
        entry = NoteEntry(
            id="abc123",
            title="测试笔记",
            description="一段简单的描述",
            body="这是正文内容",
            created_at="2026-05-20T10:00:00+08:00",
            updated_at="2026-05-20T10:00:00+08:00",
        )
        d = entry.to_dict()
        restored = NoteEntry.from_dict(d)
        self.assertEqual(entry.id, restored.id)
        self.assertEqual(entry.title, restored.title)
        self.assertEqual(entry.description, restored.description)
        self.assertEqual(entry.body, restored.body)
        self.assertEqual(entry.created_at, restored.created_at)
        self.assertEqual(entry.updated_at, restored.updated_at)

    def test_note_entry_display_title_falls_back(self) -> None:
        entry = NoteEntry(
            id="1", title="", description="", body="",
            created_at="", updated_at="",
        )
        self.assertEqual(entry.display_title, "未命名笔记")

    def test_note_entry_display_title_uses_title(self) -> None:
        entry = NoteEntry(
            id="1", title="我的笔记", description="", body="",
            created_at="", updated_at="",
        )
        self.assertEqual(entry.display_title, "我的笔记")

    def test_create_empty_note(self) -> None:
        storage = NoteStorage(self.case_dir)
        note = storage.create_empty_note()
        self.assertEqual(note.title, "")
        self.assertEqual(note.description, "")
        self.assertEqual(note.body, "")
        self.assertTrue(note.id)
        self.assertTrue(note.created_at)
        self.assertTrue(note.updated_at)

    def test_save_and_load_note(self) -> None:
        storage = NoteStorage(self.case_dir)
        note = storage.create_empty_note()
        note.title = "会议记录"
        note.description = "周会讨论要点"
        note.body = "1. 项目进度\n2. 风险排查"
        saved = storage.save_note(note)
        loaded = storage.load_note(saved.id)
        self.assertEqual(saved.title, loaded.title)
        self.assertEqual(saved.description, loaded.description)
        self.assertEqual(saved.body, loaded.body)

    def test_list_notes_returns_saved_notes(self) -> None:
        storage = NoteStorage(self.case_dir)
        note = storage.create_empty_note()
        note.title = "待办事项"
        storage.save_note(note)
        notes = storage.list_notes()
        self.assertEqual(1, len(notes))
        self.assertEqual("待办事项", notes[0].title)

    def test_list_notes_excludes_deleted(self) -> None:
        storage = NoteStorage(self.case_dir)
        note = storage.create_empty_note()
        note.title = "将被删除"
        saved = storage.save_note(note)
        storage.delete_note(saved.id)
        self.assertEqual(0, len(storage.list_notes()))

    def test_load_deleted_note_still_works(self) -> None:
        storage = NoteStorage(self.case_dir)
        note = storage.create_empty_note()
        note.title = "删除后仍可加载"
        saved = storage.save_note(note)
        storage.delete_note(saved.id)
        loaded = storage.load_note(saved.id)
        self.assertEqual(saved.id, loaded.id)

    def test_search_notes_by_keyword(self) -> None:
        storage = NoteStorage(self.case_dir)
        n1 = storage.create_empty_note()
        n1.title = "Python 学习"
        n1.description = "基础语法"
        n1.body = "变量和函数"
        storage.save_note(n1)
        n2 = storage.create_empty_note()
        n2.title = "Java 学习"
        n2.description = "面向对象"
        n2.body = "类和接口"
        storage.save_note(n2)

        results = storage.list_notes(query="Python")
        self.assertEqual(1, len(results))
        self.assertEqual("Python 学习", results[0].title)

    def test_search_notes_in_description_and_body(self) -> None:
        storage = NoteStorage(self.case_dir)
        n1 = storage.create_empty_note()
        n1.title = "标题"
        n1.description = "重要的描述"
        n1.body = "正文"
        storage.save_note(n1)
        n2 = storage.create_empty_note()
        n2.title = "另一条"
        n2.description = "无关"
        n2.body = "包含重要内容"
        storage.save_note(n2)

        results = storage.list_notes(query="重要")
        self.assertEqual(2, len(results))

    def test_list_notes_sorted_by_updated_at_desc(self) -> None:
        storage = NoteStorage(self.case_dir)
        import time
        n1 = storage.create_empty_note()
        n1.title = "旧的"
        saved1 = storage.save_note(n1)
        time.sleep(0.01)
        n2 = storage.create_empty_note()
        n2.title = "新的"
        saved2 = storage.save_note(n2)

        notes = storage.list_notes()
        self.assertEqual(2, len(notes))
        self.assertEqual("新的", notes[0].title)
        self.assertEqual("旧的", notes[1].title)


if __name__ == "__main__":
    unittest.main()
