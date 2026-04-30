from __future__ import annotations

import shutil
import sys
import unittest
import json
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from life_dairy.plan_storage import PlanStorage


class PlanStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case_dir = ROOT / ".tmp_testdata" / f"plan_case_{uuid4().hex}"
        self.case_dir.mkdir(parents=True, exist_ok=False)
        self.storage = PlanStorage(self.case_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.case_dir, ignore_errors=True)

    def test_save_reload_search_and_delete_plan(self) -> None:
        plan = self.storage.create_empty_plan()
        plan.title = "整理照片"
        plan.due_date = "2026-04-25"
        plan.status = "进行中"
        plan.priority = "高"
        plan.notes = "先把四月照片分组。"
        plan.tags = ["整理"]

        saved = self.storage.save_plan(plan)
        loaded = self.storage.load_plan(saved.id)

        self.assertEqual("整理照片", loaded.title)
        self.assertEqual("add", loaded.plan_type)
        self.assertEqual(["整理"], loaded.tags)
        self.assertEqual("进行中", loaded.status)
        self.assertEqual([saved.id], [item.id for item in self.storage.list_plans("四月照片")])
        loaded.title = "整理四月照片"
        loaded.status = "已完成"
        saved_again = self.storage.save_plan(loaded)
        self.assertEqual("已完成", self.storage.load_plan(saved_again.id).status)

        self.storage.delete_plan(saved.id)
        self.assertEqual([], self.storage.list_plans())

    def test_legacy_plan_without_type_defaults_to_add(self) -> None:
        plan_id = uuid4().hex
        plan_dir = self.storage.plan_dir(plan_id)
        plan_dir.mkdir(parents=True)
        with (plan_dir / "plan.json").open("w", encoding="utf-8") as file:
            json.dump(
                {
                    "id": plan_id,
                    "title": "旧计划",
                    "due_date": "2026-04-25",
                    "status": "未开始",
                    "priority": "普通",
                    "notes": "旧数据没有计划类型",
                    "created_at": "2026-04-25T00:00:00+08:00",
                    "updated_at": "2026-04-25T00:00:00+08:00",
                },
                file,
                ensure_ascii=False,
            )

        loaded = self.storage.load_plan(plan_id)

        self.assertEqual("add", loaded.plan_type)
        self.assertEqual("", loaded.subtract_mode)
        self.assertEqual([plan_id], [item.id for item in self.storage.list_plans("", "add")])
        self.assertEqual([], self.storage.list_plans("", "subtract"))

    def test_save_reload_search_and_filter_subtract_plan(self) -> None:
        add_plan = self.storage.create_empty_plan()
        add_plan.title = "学习材料力学"
        add_plan.tags = ["课程"]
        saved_add = self.storage.save_plan(add_plan)

        subtract_plan = self.storage.create_empty_plan()
        subtract_plan.title = "今晚不刷短视频"
        subtract_plan.plan_type = "subtract"
        subtract_plan.subtract_mode = "不做"
        subtract_plan.trigger_scene = "晚上回宿舍后感到疲惫"
        subtract_plan.avoid_behavior = "连续刷短视频超过30分钟"
        subtract_plan.reason = "影响睡眠和第二天学习状态"
        subtract_plan.alternative_action = "洗漱后听10分钟播客然后睡觉"
        subtract_plan.tags = ["睡眠", "短视频"]
        saved_subtract = self.storage.save_plan(subtract_plan)
        loaded = self.storage.load_plan(saved_subtract.id)

        self.assertEqual("subtract", loaded.plan_type)
        self.assertEqual("不做", loaded.subtract_mode)
        self.assertEqual("晚上回宿舍后感到疲惫", loaded.trigger_scene)
        self.assertEqual("连续刷短视频超过30分钟", loaded.avoid_behavior)
        self.assertEqual("影响睡眠和第二天学习状态", loaded.reason)
        self.assertEqual("洗漱后听10分钟播客然后睡觉", loaded.alternative_action)
        self.assertEqual(["睡眠", "短视频"], loaded.tags)
        self.assertEqual([saved_add.id], [item.id for item in self.storage.list_plans("", "add")])
        self.assertEqual([saved_subtract.id], [item.id for item in self.storage.list_plans("", "subtract")])
        self.assertEqual([saved_subtract.id], [item.id for item in self.storage.list_plans("疲惫")])
        self.assertEqual([saved_subtract.id], [item.id for item in self.storage.list_plans("短视频")])
        self.assertEqual([saved_subtract.id], [item.id for item in self.storage.list_plans("播客")])

    def test_saving_add_plan_clears_subtract_only_fields(self) -> None:
        plan = self.storage.create_empty_plan()
        plan.title = "普通加法计划"
        plan.plan_type = "add"
        plan.subtract_mode = "戒断"
        plan.trigger_scene = "不应保存"
        plan.avoid_behavior = "不应保存"
        plan.reason = "不应保存"
        plan.alternative_action = "不应保存"

        saved = self.storage.save_plan(plan)
        loaded = self.storage.load_plan(saved.id)

        self.assertEqual("add", loaded.plan_type)
        self.assertEqual("", loaded.subtract_mode)
        self.assertEqual("", loaded.trigger_scene)
        self.assertEqual("", loaded.avoid_behavior)
        self.assertEqual("", loaded.reason)
        self.assertEqual("", loaded.alternative_action)


if __name__ == "__main__":
    unittest.main()
