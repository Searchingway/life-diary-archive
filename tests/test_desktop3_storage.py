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
from life_dairy.observation_storage import ObservationStorage
from life_dairy.resource_storage import ResourceStorage
from life_dairy.thought_storage import ThoughtStorage
from life_dairy.work_storage import WorkStorage


class Desktop3StorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case_dir = ROOT / ".tmp_testdata" / f"desktop3_case_{uuid4().hex}"
        self.case_dir.mkdir(parents=True, exist_ok=False)

    def tearDown(self) -> None:
        shutil.rmtree(self.case_dir, ignore_errors=True)

    def test_thought_storage_saves_filters_and_soft_deletes(self) -> None:
        storage = ThoughtStorage(self.case_dir)
        thought = storage.create_empty_thought()
        thought.title = "要不要接这个需求"
        thought.thought_type = "接单思考"
        thought.status = "思考中"
        thought.ideas.append({"time": "2026-05-02T10:00:00+08:00", "text": "先看时间成本"})
        saved = storage.save_thought(thought)

        self.assertEqual(saved.id, storage.list_thoughts("时间", "接单思考", "思考中")[0].id)

        storage.delete_thought(saved.id)
        self.assertEqual([], storage.list_thoughts())

    def test_resource_storage_saves_resource_items_and_recurrence_test(self) -> None:
        storage = ResourceStorage(self.case_dir)
        resource = storage.create_empty_resource()
        resource.title = "周末加班"
        resource.resource_type = "项目"
        resource.resource_items = [
            {
                "type": "时间",
                "direct_time": "3 小时",
                "indirect_time": "1 小时沟通",
                "recovery_time": "半天",
                "time_block_interrupt": "毁掉半天",
            },
            {"type": "金钱", "amount": 2000, "cycle": "一次性", "direction": "收入"},
        ]
        resource.recurrence_test = {
            "next_week": "不愿意",
            "one_year": "会很累",
            "repeat_willingness": "不主动重复",
        }
        saved = storage.save_resource(resource)
        loaded = storage.load_resource(saved.id)

        self.assertEqual(2, len(loaded.resource_items))
        self.assertEqual("毁掉半天", loaded.resource_items[0]["time_block_interrupt"])
        self.assertEqual("不主动重复", loaded.recurrence_test["repeat_willingness"])

    def test_observation_storage_filters_by_emotion_intensity_and_date(self) -> None:
        storage = ObservationStorage(self.case_dir)
        observation = storage.create_empty_observation()
        observation.time = "2026-05-02T20:00:00+08:00"
        observation.emotion = "焦虑"
        observation.intensity = 4
        observation.trigger = "临时改需求"
        saved = storage.save_observation(observation)

        self.assertEqual(saved.id, storage.list_observations("改需求", "焦虑", "4", "2026-05")[0].id)

    def test_work_storage_exposes_legacy_books_as_book_type_works(self) -> None:
        book_storage = BookStorage(self.case_dir)
        book = book_storage.create_empty_book()
        book.title = "人类简史"
        book.author = "尤瓦尔"
        book.notes = "旧读书笔记正文"
        saved_book = book_storage.save_book(book)

        work_storage = WorkStorage(self.case_dir)
        works = work_storage.list_works("人类")
        loaded = work_storage.load_work(saved_book.id)

        self.assertEqual(1, len(works))
        self.assertEqual("书籍", works[0].work_type)
        self.assertEqual("人类简史", loaded.title)
        self.assertIn("旧读书笔记正文", loaded.final_review)


if __name__ == "__main__":
    unittest.main()
