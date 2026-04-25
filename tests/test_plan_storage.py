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

        saved = self.storage.save_plan(plan)
        loaded = self.storage.load_plan(saved.id)

        self.assertEqual("整理照片", loaded.title)
        self.assertEqual("进行中", loaded.status)
        self.assertEqual([saved.id], [item.id for item in self.storage.list_plans("四月照片")])

        self.storage.delete_plan(saved.id)
        self.assertEqual([], self.storage.list_plans())


if __name__ == "__main__":
    unittest.main()
