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

from life_dairy.lesson_storage import LessonStorage
from life_dairy.models import LessonImageDraft, LessonRelatedDiary


class LessonStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case_dir = ROOT / ".tmp_testdata" / f"lesson_case_{uuid4().hex}"
        self.case_dir.mkdir(parents=True, exist_ok=False)
        self.storage = LessonStorage(self.case_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.case_dir, ignore_errors=True)

    def test_save_and_reload_lesson(self) -> None:
        lesson = self.storage.create_empty_lesson()
        lesson.title = "接单报价失误"
        lesson.date = "2026-04-30"
        lesson.category = "接单"
        lesson.severity = "重要"
        lesson.tags = ["报价", "沟通"]
        lesson.event = "客户临时增加范围。"
        lesson.judgment = "我以为只是小改动。"
        lesson.result = "项目时间被压缩。"
        lesson.mistake = "没有重新确认边界。"
        lesson.root_cause = "害怕推进变慢。"
        lesson.cost = "多花了两个晚上。"
        lesson.next_action = "以后范围变化先冻结需求，再重新报价。"
        lesson.one_sentence = "范围没定清楚，就不要急着答应。"
        lesson.related_diaries.append(
            LessonRelatedDiary(entry_id="entry-1", date="2026-04-29", title="项目沟通")
        )

        saved = self.storage.save_lesson(lesson)
        loaded = self.storage.load_lesson(saved.id)

        self.assertEqual("接单报价失误", loaded.title)
        self.assertEqual("接单", loaded.category)
        self.assertEqual("重要", loaded.severity)
        self.assertEqual(["报价", "沟通"], loaded.tags)
        self.assertEqual("客户临时增加范围。", loaded.event)
        self.assertEqual("我以为只是小改动。", loaded.judgment)
        self.assertEqual("项目时间被压缩。", loaded.result)
        self.assertEqual("没有重新确认边界。", loaded.mistake)
        self.assertEqual("害怕推进变慢。", loaded.root_cause)
        self.assertEqual("多花了两个晚上。", loaded.cost)
        self.assertEqual("以后范围变化先冻结需求，再重新报价。", loaded.next_action)
        self.assertEqual("范围没定清楚，就不要急着答应。", loaded.one_sentence)
        self.assertEqual("2026-04-29", loaded.related_diaries[0].date)
        self.assertTrue((self.storage.lesson_dir(saved.id) / "lesson.json").exists())
        self.assertTrue((self.storage.lesson_dir(saved.id) / "content.md").exists())

    def test_list_lessons_can_search_title_tags_body_and_filter_category(self) -> None:
        first = self.storage.create_empty_lesson()
        first.title = "学习节奏反思"
        first.category = "学习"
        first.tags = ["复盘", "算法"]
        first.event = "刷题时跳过了错题整理。"
        first.next_action = "每晚固定整理错题。"
        self.storage.save_lesson(first)

        second = self.storage.create_empty_lesson()
        second.title = "接单沟通"
        second.category = "接单"
        second.tags = ["客户"]
        second.event = "没有保留书面确认。"
        self.storage.save_lesson(second)

        self.assertEqual([first.id], [item.id for item in self.storage.list_lessons("学习节奏")])
        self.assertEqual([first.id], [item.id for item in self.storage.list_lessons("算法")])
        self.assertEqual([first.id], [item.id for item in self.storage.list_lessons("错题")])
        self.assertEqual([second.id], [item.id for item in self.storage.list_lessons("", "接单")])
        self.assertEqual([], [item.id for item in self.storage.list_lessons("错题", "接单")])

    def test_delete_lesson_hides_item_from_active_list(self) -> None:
        lesson = self.storage.create_empty_lesson()
        saved = self.storage.save_lesson(lesson)

        self.storage.delete_lesson(saved.id)

        self.assertTrue(self.storage.lesson_dir(saved.id).exists())
        self.assertEqual([], self.storage.list_lessons())

    def test_save_reload_and_remove_images_with_label(self) -> None:
        image_one = self.case_dir / "screen.jpg"
        image_two = self.case_dir / "chat.png"
        image_one.write_bytes(b"jpeg-data")
        image_two.write_bytes(b"png-data")

        lesson = self.storage.create_empty_lesson()
        saved = self.storage.save_lesson(
            lesson,
            [
                LessonImageDraft(source_path=image_one, label="现场截图"),
                LessonImageDraft(source_path=image_two, label="沟通记录"),
            ],
        )
        loaded = self.storage.load_lesson(saved.id)

        self.assertEqual(["现场截图", "沟通记录"], [item.label for item in loaded.images])
        kept = loaded.images[0]
        kept_path = self.storage.resolve_image_path(saved.id, kept.file_name)
        saved_again = self.storage.save_lesson(
            loaded,
            [LessonImageDraft(source_path=kept_path, label=kept.label)],
        )

        self.assertEqual([kept.file_name], [item.file_name for item in saved_again.images])
        self.assertTrue(kept_path.exists())


if __name__ == "__main__":
    unittest.main()
