from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from uuid import uuid4

from .models import now_iso

ACTION_PLAN_STATUSES = ["未开始", "进行中", "暂停", "已完成", "放弃"]
ACTION_PLAN_TYPES = ["学习", "接单", "项目", "生活", "身体", "武术", "情绪", "长期目标", "其他"]

STATUS_ORDER = {"进行中": 0, "未开始": 1, "暂停": 2, "已完成": 3, "放弃": 4}
PRIORITY_ORDER = {"高": 0, "普通": 1, "低": 2}


@dataclass(slots=True)
class ActionPlanTask:
    id: str
    title: str
    date: str
    estimated_minutes: int = 0
    done: bool = False
    note: str = ""
    x: float | None = None
    y: float | None = None

    def to_dict(self) -> dict:
        d: dict = {
            "id": self.id,
            "title": self.title,
            "date": self.date,
            "estimated_minutes": self.estimated_minutes,
            "done": self.done,
            "note": self.note,
        }
        if self.x is not None:
            d["x"] = self.x
        if self.y is not None:
            d["y"] = self.y
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "ActionPlanTask":
        return cls(
            id=str(data.get("id", uuid4().hex)),
            title=str(data.get("title", "")),
            date=str(data.get("date", "")),
            estimated_minutes=int(data.get("estimated_minutes", 0)),
            done=bool(data.get("done", False)),
            note=str(data.get("note", "")),
            x=float(data["x"]) if "x" in data and data["x"] is not None else None,
            y=float(data["y"]) if "y" in data and data["y"] is not None else None,
        )


@dataclass(slots=True)
class ActionPlanItem:
    id: str
    title: str
    plan_type: str
    description: str
    start_date: str
    end_date: str
    daily_available_time: str
    priority: str
    status: str
    source_light_plan_id: str
    tasks: list[ActionPlanTask] = field(default_factory=list)
    summary: str = ""
    created_at: str = ""
    updated_at: str = ""

    @property
    def display_title(self) -> str:
        return self.title.strip() or "未命名行动计划"

    @property
    def progress(self) -> float:
        if not self.tasks:
            return 0.0
        done_count = sum(1 for t in self.tasks if t.done)
        return round(done_count / len(self.tasks) * 100, 1)

    @property
    def today_tasks(self) -> list[ActionPlanTask]:
        today_str = date.today().isoformat()
        return [t for t in self.tasks if t.date == today_str and not t.done]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "plan_type": self.plan_type,
            "description": self.description,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "daily_available_time": self.daily_available_time,
            "priority": self.priority,
            "status": self.status,
            "source_light_plan_id": self.source_light_plan_id,
            "tasks": [t.to_dict() for t in self.tasks],
            "summary": self.summary,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ActionPlanItem":
        tasks = [ActionPlanTask.from_dict(t) for t in data.get("tasks", [])]
        return cls(
            id=str(data["id"]),
            title=str(data.get("title", "")),
            plan_type=str(data.get("plan_type", "其他")),
            description=str(data.get("description", "")),
            start_date=str(data.get("start_date", "")),
            end_date=str(data.get("end_date", "")),
            daily_available_time=str(data.get("daily_available_time", "")),
            priority=str(data.get("priority", "普通")),
            status=str(data.get("status", "未开始")),
            source_light_plan_id=str(data.get("source_light_plan_id", "")),
            tasks=tasks,
            summary=str(data.get("summary", "")),
            created_at=str(data.get("created_at", "")),
            updated_at=str(data.get("updated_at", "")),
        )


class ActionPlanStorage:
    def __init__(self, root_dir: Path | str):
        self.root_dir = Path(root_dir)
        self.plans_dir = self.root_dir / "action_plans"
        self.plans_dir.mkdir(parents=True, exist_ok=True)

    def create_empty_plan(self) -> ActionPlanItem:
        timestamp = now_iso()
        return ActionPlanItem(
            id=uuid4().hex,
            title="",
            plan_type="其他",
            description="",
            start_date=date.today().isoformat(),
            end_date="",
            daily_available_time="",
            priority="普通",
            status="未开始",
            source_light_plan_id="",
            tasks=[],
            summary="",
            created_at=timestamp,
            updated_at=timestamp,
        )

    def plan_dir(self, plan_id: str) -> Path:
        return self.plans_dir / plan_id

    def list_plans(
        self,
        query: str = "",
        status_filter: str = "全部",
        plan_type_filter: str = "全部",
    ) -> list[ActionPlanItem]:
        keyword = query.strip().lower()
        items: list[ActionPlanItem] = []
        for child in self.plans_dir.iterdir():
            if not child.is_dir():
                continue
            try:
                item = self._load_plan_from_directory(child, include_deleted=False)
            except (FileNotFoundError, KeyError, json.JSONDecodeError, OSError, ValueError):
                continue
            if status_filter not in ("全部", "") and item.status != status_filter:
                continue
            if plan_type_filter not in ("全部", "") and item.plan_type != plan_type_filter:
                continue
            if keyword and not self._matches_query(item, keyword):
                continue
            items.append(item)

        items.sort(
            key=lambda item: (
                STATUS_ORDER.get(item.status, 9),
                PRIORITY_ORDER.get(item.priority, 9),
                item.end_date or "9999-99-99",
            )
        )
        return items

    def save_plan(self, plan: ActionPlanItem) -> ActionPlanItem:
        plan_dir = self.plan_dir(plan.id)
        plan_dir.mkdir(parents=True, exist_ok=True)
        plan.updated_at = now_iso()
        if plan.plan_type not in ACTION_PLAN_TYPES:
            plan.plan_type = "其他"
        if plan.status not in ACTION_PLAN_STATUSES:
            plan.status = "未开始"
        with (plan_dir / "action_plan.json").open("w", encoding="utf-8") as f:
            json.dump(plan.to_dict(), f, ensure_ascii=False, indent=2)
        return self.load_plan(plan.id)

    def load_plan(self, plan_id: str) -> ActionPlanItem:
        return self._load_plan_from_directory(self.plan_dir(plan_id), include_deleted=True)

    def delete_plan(self, plan_id: str) -> None:
        plan_dir = self.plan_dir(plan_id)
        if not plan_dir.exists():
            raise FileNotFoundError(f"找不到要删除的行动计划：{plan_id}")
        metadata_path = plan_dir / "action_plan.json"
        with metadata_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        data["deleted"] = True
        data["deleted_at"] = now_iso()
        data["updated_at"] = now_iso()
        with metadata_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_plan_from_directory(self, plan_dir: Path, include_deleted: bool) -> ActionPlanItem:
        with (plan_dir / "action_plan.json").open("r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("deleted") and not include_deleted:
            raise ValueError("action plan deleted")
        return ActionPlanItem.from_dict(data)

    def _matches_query(self, plan: ActionPlanItem, keyword: str) -> bool:
        haystacks = [
            plan.title,
            plan.description,
            plan.plan_type,
            plan.status,
            plan.priority,
            plan.summary,
            plan.start_date,
            plan.end_date,
            plan.daily_available_time,
        ]
        for task in plan.tasks:
            haystacks.extend([task.title, task.note, task.date])
        return any(keyword in (text or "").lower() for text in haystacks)
