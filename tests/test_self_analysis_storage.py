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

from life_dairy.models import (
    SelfAnalysisImageDraft,
    SelfAnalysisRelatedDiary,
    SelfAnalysisRelatedLesson,
)
from life_dairy.self_analysis_storage import SelfAnalysisStorage


class SelfAnalysisStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case_dir = ROOT / ".tmp_testdata" / f"self_analysis_case_{uuid4().hex}"
        self.case_dir.mkdir(parents=True, exist_ok=False)
        self.storage = SelfAnalysisStorage(self.case_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.case_dir, ignore_errors=True)

    def test_save_and_reload_analysis_with_relations(self) -> None:
        analysis = self.storage.create_empty_analysis()
        analysis.title = "接单焦虑复盘"
        analysis.date = "2026-05-01"
        analysis.analysis_type = "接单焦虑"
        analysis.tags = ["报价", "边界"]
        analysis.trigger_event = "客户临时追问能不能今晚交付。"
        analysis.emotion = "紧张，怕被认为不专业。"
        analysis.body_reaction = "肩颈发紧。"
        analysis.surface_want = "想立刻答应。"
        analysis.real_fear = "害怕失去订单。"
        analysis.real_want = "想要清楚边界和稳定节奏。"
        analysis.repeated_pattern = "先答应，后焦虑。"
        analysis.imagined_judgment = "别人会觉得我不够快。"
        analysis.defense = "讨好和过度承诺。"
        analysis.similar_experience = "以前报价没说清范围。"
        analysis.insight = "焦虑来自边界不清，而不是能力不足。"
        analysis.next_action = "先确认范围、时间和价格，再答复。"
        analysis.related_diaries.append(
            SelfAnalysisRelatedDiary(entry_id="entry-1", date="2026-05-01", title="客户沟通")
        )
        analysis.related_lessons.append(
            SelfAnalysisRelatedLesson(lesson_id="lesson-1", date="2026-04-30", title="报价边界反思")
        )

        saved = self.storage.save_analysis(analysis)
        loaded = self.storage.load_analysis(saved.id)

        self.assertEqual("接单焦虑复盘", loaded.title)
        self.assertEqual("接单焦虑", loaded.analysis_type)
        self.assertEqual(["报价", "边界"], loaded.tags)
        self.assertEqual("客户临时追问能不能今晚交付。", loaded.trigger_event)
        self.assertEqual("紧张，怕被认为不专业。", loaded.emotion)
        self.assertEqual("肩颈发紧。", loaded.body_reaction)
        self.assertEqual("想立刻答应。", loaded.surface_want)
        self.assertEqual("害怕失去订单。", loaded.real_fear)
        self.assertEqual("想要清楚边界和稳定节奏。", loaded.real_want)
        self.assertEqual("先答应，后焦虑。", loaded.repeated_pattern)
        self.assertEqual("别人会觉得我不够快。", loaded.imagined_judgment)
        self.assertEqual("讨好和过度承诺。", loaded.defense)
        self.assertEqual("以前报价没说清范围。", loaded.similar_experience)
        self.assertEqual("焦虑来自边界不清，而不是能力不足。", loaded.insight)
        self.assertEqual("先确认范围、时间和价格，再答复。", loaded.next_action)
        self.assertEqual("entry-1", loaded.related_diaries[0].entry_id)
        self.assertEqual("lesson-1", loaded.related_lessons[0].lesson_id)
        self.assertTrue((self.storage.analysis_dir(saved.id) / "analysis.json").exists())
        self.assertTrue((self.storage.analysis_dir(saved.id) / "content.md").exists())

        loaded.insight = "编辑后确认：关键仍然是先定边界。"
        edited = self.storage.save_analysis(loaded)
        reopened = self.storage.load_analysis(edited.id)
        self.assertEqual("编辑后确认：关键仍然是先定边界。", reopened.insight)

    def test_list_analyses_can_search_title_tags_body_and_filter_type(self) -> None:
        first = self.storage.create_empty_analysis()
        first.title = "学习困境观察"
        first.analysis_type = "学习困境"
        first.tags = ["算法", "拖延"]
        first.trigger_event = "看到错题就想跳过。"
        first.insight = "真正卡住的是复盘流程。"
        self.storage.save_analysis(first)

        second = self.storage.create_empty_analysis()
        second.title = "梦境记录"
        second.analysis_type = "梦"
        second.tags = ["夜间"]
        second.trigger_event = "梦见赶车迟到。"
        self.storage.save_analysis(second)

        self.assertEqual([first.id], [item.id for item in self.storage.list_analyses("学习困境")])
        self.assertEqual([first.id], [item.id for item in self.storage.list_analyses("算法")])
        self.assertEqual([first.id], [item.id for item in self.storage.list_analyses("复盘流程")])
        self.assertEqual([second.id], [item.id for item in self.storage.list_analyses("", "梦")])
        self.assertEqual([], [item.id for item in self.storage.list_analyses("复盘流程", "梦")])

    def test_delete_analysis_hides_item_from_active_list(self) -> None:
        analysis = self.storage.create_empty_analysis()
        saved = self.storage.save_analysis(analysis)

        self.storage.delete_analysis(saved.id)

        self.assertTrue(self.storage.analysis_dir(saved.id).exists())
        self.assertEqual([], self.storage.list_analyses())

    def test_save_reload_and_remove_images_with_label(self) -> None:
        image_one = self.case_dir / "screen.jpg"
        image_two = self.case_dir / "note.png"
        image_one.write_bytes(b"jpeg-data")
        image_two.write_bytes(b"png-data")

        analysis = self.storage.create_empty_analysis()
        saved = self.storage.save_analysis(
            analysis,
            [
                SelfAnalysisImageDraft(source_path=image_one, label="聊天截图"),
                SelfAnalysisImageDraft(source_path=image_two, label="手写备注"),
            ],
        )
        loaded = self.storage.load_analysis(saved.id)

        self.assertEqual(["聊天截图", "手写备注"], [item.label for item in loaded.images])
        kept = loaded.images[0]
        kept_path = self.storage.resolve_image_path(saved.id, kept.file_name)
        saved_again = self.storage.save_analysis(
            loaded,
            [SelfAnalysisImageDraft(source_path=kept_path, label=kept.label)],
        )

        self.assertEqual([kept.file_name], [item.file_name for item in saved_again.images])
        self.assertTrue(kept_path.exists())


if __name__ == "__main__":
    unittest.main()
