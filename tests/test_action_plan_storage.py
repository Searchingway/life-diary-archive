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

from life_dairy.action_plan_storage import (
    ActionPlanItem,
    ActionPlanStorage,
    ActionPlanTask,
)


class ActionPlanStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case_dir = ROOT / ".tmp_testdata" / f"ap_case_{uuid4().hex}"
        self.case_dir.mkdir(parents=True, exist_ok=False)
        self.storage = ActionPlanStorage(self.case_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.case_dir, ignore_errors=True)

    def test_create_empty_plan_has_defaults(self) -> None:
        plan = self.storage.create_empty_plan()
        self.assertEqual("", plan.title)
        self.assertEqual("未开始", plan.status)
        self.assertEqual("普通", plan.priority)
        self.assertEqual("其他", plan.plan_type)
        self.assertEqual([], plan.tasks)
        self.assertEqual(0.0, plan.progress)

    def test_save_reload_search_and_delete(self) -> None:
        plan = self.storage.create_empty_plan()
        plan.title = "完成双端数据互通测试"
        plan.plan_type = "项目"
        plan.status = "进行中"
        plan.priority = "高"
        plan.description = "测试 ZIP 数据互通"
        plan.start_date = "2026-05-20"
        plan.end_date = "2026-05-27"
        plan.daily_available_time = "1小时"

        task1 = ActionPlanTask(
            id=uuid4().hex,
            title="整理测试清单",
            date="2026-05-20",
            estimated_minutes=40,
            done=False,
            note="确认三条主流程",
        )
        task2 = ActionPlanTask(
            id=uuid4().hex,
            title="修复导出问题",
            date="2026-05-21",
            estimated_minutes=60,
            done=True,
        )
        plan.tasks = [task1, task2]

        saved = self.storage.save_plan(plan)
        loaded = self.storage.load_plan(saved.id)

        self.assertEqual("完成双端数据互通测试", loaded.title)
        self.assertEqual("项目", loaded.plan_type)
        self.assertEqual("进行中", loaded.status)
        self.assertEqual("高", loaded.priority)
        self.assertEqual(2, len(loaded.tasks))
        self.assertEqual(50.0, loaded.progress)
        self.assertFalse(loaded.tasks[0].done)
        self.assertTrue(loaded.tasks[1].done)

        self.assertEqual(
            [saved.id],
            [item.id for item in self.storage.list_plans("数据互通")],
        )

        self.storage.delete_plan(saved.id)
        self.assertEqual([], self.storage.list_plans())

    def test_list_plans_filters_by_status(self) -> None:
        plan1 = self.storage.create_empty_plan()
        plan1.title = "进行中计划"
        plan1.status = "进行中"
        self.storage.save_plan(plan1)

        plan2 = self.storage.create_empty_plan()
        plan2.title = "已完成计划"
        plan2.status = "已完成"
        self.storage.save_plan(plan2)

        self.assertEqual(1, len(self.storage.list_plans(status_filter="进行中")))
        self.assertEqual(1, len(self.storage.list_plans(status_filter="已完成")))
        self.assertEqual(2, len(self.storage.list_plans()))

    def test_list_plans_filters_by_type(self) -> None:
        plan1 = self.storage.create_empty_plan()
        plan1.title = "学习计划"
        plan1.plan_type = "学习"
        self.storage.save_plan(plan1)

        plan2 = self.storage.create_empty_plan()
        plan2.title = "身体计划"
        plan2.plan_type = "身体"
        self.storage.save_plan(plan2)

        self.assertEqual(1, len(self.storage.list_plans(plan_type_filter="学习")))
        self.assertEqual(1, len(self.storage.list_plans(plan_type_filter="身体")))

    def test_search_finds_content_in_tasks(self) -> None:
        plan = self.storage.create_empty_plan()
        plan.title = "测试计划"
        plan.tasks = [
            ActionPlanTask(
                id=uuid4().hex,
                title="写单元测试",
                date="2026-05-20",
                note="覆盖所有存储方法",
            )
        ]
        self.storage.save_plan(plan)

        self.assertEqual(1, len(self.storage.list_plans("单元测试")))
        self.assertEqual(1, len(self.storage.list_plans("存储方法")))

    def test_progress_zero_for_empty_tasks(self) -> None:
        plan = self.storage.create_empty_plan()
        self.assertEqual(0.0, plan.progress)

    def test_progress_full_when_all_done(self) -> None:
        plan = self.storage.create_empty_plan()
        plan.tasks = [
            ActionPlanTask(id=uuid4().hex, title="t1", date="2026-05-20", done=True),
            ActionPlanTask(id=uuid4().hex, title="t2", date="2026-05-21", done=True),
        ]
        self.assertEqual(100.0, plan.progress)

    def test_today_tasks_returns_only_undone_today(self) -> None:
        from datetime import date as dt

        plan = self.storage.create_empty_plan()
        today = dt.today().isoformat()
        plan.tasks = [
            ActionPlanTask(id=uuid4().hex, title="today task", date=today, done=False),
            ActionPlanTask(id=uuid4().hex, title="done today", date=today, done=True),
            ActionPlanTask(id=uuid4().hex, title="future task", date="2099-12-31", done=False),
        ]
        today_tasks = plan.today_tasks
        self.assertEqual(1, len(today_tasks))
        self.assertEqual("today task", today_tasks[0].title)

    def test_reload_after_save_preserves_data(self) -> None:
        plan = self.storage.create_empty_plan()
        plan.title = "重启后验证"
        plan.tasks = [
            ActionPlanTask(id=uuid4().hex, title="验证任务", date="2026-05-20", done=False)
        ]
        saved = self.storage.save_plan(plan)

        storage2 = ActionPlanStorage(self.case_dir)
        loaded = storage2.load_plan(saved.id)
        self.assertEqual("重启后验证", loaded.title)
        self.assertEqual(1, len(loaded.tasks))
        self.assertFalse(loaded.tasks[0].done)


if __name__ == "__main__":
    unittest.main()
