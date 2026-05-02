from __future__ import annotations

import shutil
import sys
import unittest
from datetime import date
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from life_dairy.book_storage import BookStorage
from life_dairy.footprint_storage import FootprintStorage
from life_dairy.lesson_storage import LessonStorage
from life_dairy.models import DiaryImageDraft
from life_dairy.observation_storage import ObservationStorage
from life_dairy.overview import OverviewService
from life_dairy.plan_storage import PlanStorage
from life_dairy.resource_storage import ResourceStorage
from life_dairy.self_analysis_storage import SelfAnalysisStorage
from life_dairy.storage import DiaryStorage
from life_dairy.thought_storage import ThoughtStorage
from life_dairy.work_storage import WorkStorage


class OverviewServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case_dir = ROOT / ".tmp_testdata" / f"overview_case_{uuid4().hex}"
        self.case_dir.mkdir(parents=True, exist_ok=False)
        self.diary_storage = DiaryStorage(self.case_dir)
        self.footprint_storage = FootprintStorage(self.case_dir)
        self.book_storage = BookStorage(self.case_dir)
        self.plan_storage = PlanStorage(self.case_dir)
        self.lesson_storage = LessonStorage(self.case_dir)
        self.self_analysis_storage = SelfAnalysisStorage(self.case_dir)
        self.work_storage = WorkStorage(self.case_dir)
        self.thought_storage = ThoughtStorage(self.case_dir)
        self.resource_storage = ResourceStorage(self.case_dir)
        self.observation_storage = ObservationStorage(self.case_dir)
        self.service = OverviewService(
            self.diary_storage,
            self.footprint_storage,
            self.book_storage,
            self.plan_storage,
            self.lesson_storage,
            self.self_analysis_storage,
            self.work_storage,
            self.thought_storage,
            self.resource_storage,
            self.observation_storage,
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.case_dir, ignore_errors=True)

    def test_stats_count_diary_chars_images_and_completed_plans(self) -> None:
        image_source = self.case_dir / "diary.jpg"
        image_source.write_bytes(b"jpeg-data")

        first = self.diary_storage.create_empty_entry()
        first.date = "2026-04-03"
        first.title = "本月日记"
        first.body = "今天写了一个总览页。"
        self.diary_storage.save_entry(first, [DiaryImageDraft(source_path=image_source, label="截图")])

        second = self.diary_storage.create_empty_entry()
        second.date = "2026-02-01"
        second.title = "今年旧日记"
        second.body = "二月记录"
        self.diary_storage.save_entry(second)

        completed = self.plan_storage.create_empty_plan()
        completed.title = "完成总览 MVP"
        completed.due_date = "2026-04-04"
        completed.status = "已完成"
        self.plan_storage.save_plan(completed)

        subtract_done = self.plan_storage.create_empty_plan()
        subtract_done.title = "不刷短视频"
        subtract_done.due_date = "2026-04-05"
        subtract_done.plan_type = "subtract"
        subtract_done.status = "已做到"
        self.plan_storage.save_plan(subtract_done)

        pending = self.plan_storage.create_empty_plan()
        pending.title = "未完成计划"
        pending.due_date = "2026-04-06"
        pending.status = "未开始"
        self.plan_storage.save_plan(pending)

        stats = self.service.build_stats(today=date(2026, 4, 30))

        self.assertEqual(1, stats.month_diary_count)
        self.assertEqual(len("今天写了一个总览页。"), stats.month_diary_chars)
        self.assertEqual(1, stats.month_diary_images)
        self.assertEqual(2, stats.month_completed_plans)
        self.assertEqual(2, stats.year_diary_count)
        self.assertEqual(len("今天写了一个总览页。") + len("二月记录"), stats.year_diary_chars)
        self.assertEqual(1, stats.year_diary_images)
        self.assertEqual(2, stats.year_completed_plans)

    def test_timeline_includes_all_modules_and_sorts_by_date_desc(self) -> None:
        diary = self.diary_storage.create_empty_entry()
        diary.date = "2026-04-30"
        diary.title = "日记标题"
        diary.body = "日记正文摘要"
        self.diary_storage.save_entry(diary)

        place = self.footprint_storage.create_empty_place()
        place.place_name = "南湖"
        visit = self.footprint_storage.create_empty_visit("2026-04-29")
        visit.thought = "足迹感悟摘要"
        place.visits.append(visit)
        self.footprint_storage.save_place(place)

        book = self.book_storage.create_empty_book()
        book.title = "读书标题"
        book.start_date = "2026-04-28"
        book.notes = "读书笔记摘要"
        self.book_storage.save_book(book)

        plan = self.plan_storage.create_empty_plan()
        plan.title = "计划标题"
        plan.due_date = "2026-04-27"
        plan.status = "已完成"
        self.plan_storage.save_plan(plan)

        lesson = self.lesson_storage.create_empty_lesson()
        lesson.title = "反思标题"
        lesson.date = "2026-04-26"
        lesson.event = "反思正文摘要"
        self.lesson_storage.save_lesson(lesson)

        items = self.service.build_timeline()
        record_types = [item.record_type for item in items]

        self.assertEqual(["日记", "足迹", "作品感悟", "计划", "教训"], record_types[:5])
        self.assertEqual(
            sorted([item.date for item in items], reverse=True),
            [item.date for item in items],
        )
        self.assertIn("日记正文摘要", items[0].summary)
        self.assertIn("足迹感悟摘要", items[1].summary)
        self.assertIn("读书笔记摘要", items[2].summary)
        self.assertEqual("已完成", items[3].status)
        self.assertIn("反思正文摘要", items[4].summary)

    def test_timeline_includes_desktop3_modules_and_module_summary(self) -> None:
        analysis = self.self_analysis_storage.create_empty_analysis()
        analysis.title = "焦虑反复出现"
        analysis.date = "2026-05-05"
        analysis.emotion = "焦虑"
        self.self_analysis_storage.save_analysis(analysis)

        work = self.work_storage.create_empty_work()
        work.title = "一部电影"
        work.work_type = "电影"
        work.start_date = "2026-05-04"
        work.one_sentence = "看完之后想到自己"
        self.work_storage.save_work(work)

        thought = self.thought_storage.create_empty_thought()
        thought.title = "要不要接单"
        thought.description = "时间可能不够"
        self.thought_storage.save_thought(thought)

        resource = self.resource_storage.create_empty_resource()
        resource.title = "周末加班"
        resource.overall_judgement = "会毁掉一天"
        self.resource_storage.save_resource(resource)

        observation = self.observation_storage.create_empty_observation()
        observation.time = "2026-05-03T20:00:00+08:00"
        observation.emotion = "焦虑"
        observation.trigger = "客户催进度"
        self.observation_storage.save_observation(observation)

        items = self.service.build_timeline(20)
        record_types = {item.record_type for item in items}
        stats = self.service.build_stats(today=date(2026, 5, 5))

        self.assertIn("自我分析", record_types)
        self.assertIn("作品感悟", record_types)
        self.assertIn("轻思考", record_types)
        self.assertIn("轻资源", record_types)
        self.assertIn("自我观察", record_types)
        self.assertEqual(1, stats.module_counts["轻思考"])
        self.assertEqual(1, stats.module_counts["轻资源"])
        self.assertEqual(1, stats.module_counts["自我观察"])


if __name__ == "__main__":
    unittest.main()
