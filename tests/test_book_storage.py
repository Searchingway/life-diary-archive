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

from life_dairy.book_storage import BookStorage
from life_dairy.models import BookImageDraft, BookRelatedDiary


class BookStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case_dir = ROOT / ".tmp_testdata" / f"book_case_{uuid4().hex}"
        self.case_dir.mkdir(parents=True, exist_ok=False)
        self.storage = BookStorage(self.case_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.case_dir, ignore_errors=True)

    def test_save_and_reload_book(self) -> None:
        book = self.storage.create_empty_book()
        book.title = "置身事内"
        book.author = "兰小欢"
        book.status = "在读"
        book.start_date = "2026-04-01"
        book.finish_date = ""
        book.tags = ["经济", "中国"]
        book.summary = "读中国政府与经济。"
        book.notes = "第三章很有启发。"
        book.related_diaries.append(
            BookRelatedDiary(entry_id="entry-1", date="2026-04-24", title="读书夜")
        )

        saved = self.storage.save_book(book)
        loaded = self.storage.load_book(saved.id)

        self.assertEqual("置身事内", loaded.title)
        self.assertEqual("兰小欢", loaded.author)
        self.assertEqual("在读", loaded.status)
        self.assertEqual(["经济", "中国"], loaded.tags)
        self.assertEqual("读中国政府与经济。", loaded.summary)
        self.assertEqual("第三章很有启发。", loaded.notes)
        self.assertEqual(1, len(loaded.related_diaries))
        self.assertEqual("2026-04-24", loaded.related_diaries[0].date)

    def test_list_books_can_search_title_author_tags_summary_notes_and_related_diary(self) -> None:
        first = self.storage.create_empty_book()
        first.title = "人类简史"
        first.author = "尤瓦尔"
        first.tags = ["历史", "思考"]
        first.summary = "从大历史看人类发展。"
        first.notes = "农业革命那段很有意思。"
        first.related_diaries.append(
            BookRelatedDiary(entry_id="entry-a", date="2026-04-24", title="周末读书")
        )
        self.storage.save_book(first)

        second = self.storage.create_empty_book()
        second.title = "小说课"
        second.author = "毕飞宇"
        second.tags = ["写作"]
        second.summary = "读小说的方式。"
        second.notes = "人物分析很细。"
        self.storage.save_book(second)

        self.assertEqual(["人类简史"], [item.title for item in self.storage.list_books("简史")])
        self.assertEqual(["人类简史"], [item.title for item in self.storage.list_books("尤瓦尔")])
        self.assertEqual(["人类简史"], [item.title for item in self.storage.list_books("历史")])
        self.assertEqual(["人类简史"], [item.title for item in self.storage.list_books("农业革命")])
        self.assertEqual(["人类简史"], [item.title for item in self.storage.list_books("2026-04-24")])
        self.assertEqual(["人类简史"], [item.title for item in self.storage.list_books("周末读书")])

    def test_delete_book_hides_item_from_active_list(self) -> None:
        book = self.storage.create_empty_book()
        saved = self.storage.save_book(book)

        self.storage.delete_book(saved.id)

        self.assertTrue(self.storage.book_dir(saved.id).exists())
        self.assertEqual([], self.storage.list_books())

    def test_save_and_reload_images_with_label(self) -> None:
        image_one = self.case_dir / "cover.jpg"
        image_two = self.case_dir / "note.png"
        image_one.write_bytes(b"jpeg-data")
        image_two.write_bytes(b"png-data")

        book = self.storage.create_empty_book()
        saved = self.storage.save_book(
            book,
            [
                BookImageDraft(source_path=image_one, label="书封"),
                BookImageDraft(source_path=image_two, label="摘记页"),
            ],
        )
        loaded = self.storage.load_book(saved.id)

        self.assertEqual(2, len(loaded.images))
        self.assertEqual("书封", loaded.images[0].label)
        self.assertEqual("摘记页", loaded.images[1].label)
        self.assertTrue(self.storage.resolve_image_path(saved.id, loaded.images[0].file_name).exists())


if __name__ == "__main__":
    unittest.main()
