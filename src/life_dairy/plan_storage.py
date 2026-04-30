from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from uuid import uuid4

from .models import PlanItem, now_iso


PLAN_TYPE_LABELS = {
    "add": "加法计划",
    "subtract": "减法计划",
}
PLAN_TYPE_VALUES = {
    "加法计划": "add",
    "减法计划": "subtract",
}
SUBTRACT_MODES = ["少做", "不做", "暂停", "戒断"]


class PlanStorage:
    def __init__(self, root_dir: Path | str):
        self.root_dir = Path(root_dir)
        self.plans_dir = self.root_dir / "plans"
        self.plans_dir.mkdir(parents=True, exist_ok=True)

    def create_empty_plan(self) -> PlanItem:
        timestamp = now_iso()
        return PlanItem(
            id=uuid4().hex,
            title="",
            due_date=date.today().isoformat(),
            status="未开始",
            priority="普通",
            notes="",
            tags=[],
            plan_type="add",
            subtract_mode="",
            trigger_scene="",
            avoid_behavior="",
            reason="",
            alternative_action="",
            created_at=timestamp,
            updated_at=timestamp,
        )

    def plan_dir(self, plan_id: str) -> Path:
        return self.plans_dir / plan_id

    def list_plans(self, query: str = "", plan_type_filter: str = "all") -> list[PlanItem]:
        keyword = query.strip().lower()
        items: list[PlanItem] = []
        for child in self.plans_dir.iterdir():
            if not child.is_dir():
                continue
            try:
                item = self._load_plan_from_directory(child, include_deleted=False)
            except (FileNotFoundError, KeyError, json.JSONDecodeError, OSError, ValueError):
                continue
            if plan_type_filter in {"add", "subtract"} and item.plan_type != plan_type_filter:
                continue
            if keyword and not self._matches_query(item, keyword):
                continue
            items.append(item)

        status_order = {"进行中": 0, "未开始": 1, "搁置": 2, "已完成": 3}
        items.sort(
            key=lambda item: (
                status_order.get(item.status, 9),
                item.due_date or "9999-99-99",
                item.updated_at,
            ),
        )
        return items

    def save_plan(self, plan: PlanItem) -> PlanItem:
        plan_dir = self.plan_dir(plan.id)
        plan_dir.mkdir(parents=True, exist_ok=True)

        plan.updated_at = now_iso()
        if plan.plan_type not in {"add", "subtract"}:
            plan.plan_type = "add"
        if plan.plan_type == "add":
            plan.subtract_mode = ""
            plan.trigger_scene = ""
            plan.avoid_behavior = ""
            plan.reason = ""
            plan.alternative_action = ""
        with (plan_dir / "plan.json").open("w", encoding="utf-8") as file:
            json.dump(plan.to_dict(), file, ensure_ascii=False, indent=2)
        return self.load_plan(plan.id)

    def load_plan(self, plan_id: str) -> PlanItem:
        return self._load_plan_from_directory(self.plan_dir(plan_id), include_deleted=True)

    def delete_plan(self, plan_id: str) -> None:
        plan_dir = self.plan_dir(plan_id)
        if not plan_dir.exists():
            raise FileNotFoundError(f"找不到要删除的计划：{plan_id}")
        metadata_path = plan_dir / "plan.json"
        with metadata_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        data["deleted"] = True
        data["deleted_at"] = now_iso()
        data["updated_at"] = now_iso()
        with metadata_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def _load_plan_from_directory(self, plan_dir: Path, include_deleted: bool) -> PlanItem:
        with (plan_dir / "plan.json").open("r", encoding="utf-8") as file:
            data = json.load(file)

        if data.get("deleted") and not include_deleted:
            raise ValueError("plan deleted")
        return PlanItem.from_dict(data)

    def _matches_query(self, plan: PlanItem, keyword: str) -> bool:
        haystacks = [
            plan.title,
            plan.due_date,
            plan.status,
            plan.priority,
            plan.notes,
            " ".join(plan.tags),
            PLAN_TYPE_LABELS.get(plan.plan_type, "加法计划"),
            plan.subtract_mode,
            plan.trigger_scene,
            plan.avoid_behavior,
            plan.reason,
            plan.alternative_action,
        ]
        return any(keyword in text.lower() for text in haystacks if text)
