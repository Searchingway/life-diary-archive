"""Canonical, lossless light-plan schema used by Desktop Sync Protocol V1."""
from __future__ import annotations

from copy import deepcopy
from typing import Any


PLAN_SCHEMA_VERSION = 2
PLAN_STATUSES = ("未开始", "进行中", "已暂停", "已完成")
PLAN_PRIORITIES = ("高", "中", "低")
_STATUS_ALIASES = {"暂停": "已暂停", "已暂停": "已暂停", "未开始": "未开始", "进行中": "进行中", "已完成": "已完成"}
_PRIORITY_ALIASES = {"普通": "中", "中": "中", "高": "高", "低": "低"}


def migrate_plan_to_v2(value: dict[str, Any]) -> dict[str, Any]:
    """Return a V2 plan without discarding unknown or historical fields.

    The result deliberately keeps unrecognised fields so an older mobile client
    can round-trip data it does not yet render.  Known aliases are normalised to
    their V2 names; a second migration therefore produces the same document.
    """
    source = deepcopy(value) if isinstance(value, dict) else {}
    plan_id = str(source.get("id") or source.get("plan_id") or "")
    status = _STATUS_ALIASES.get(str(source.get("status") or ""), str(source.get("status") or "未开始"))
    if status not in PLAN_STATUSES:
        status = "未开始"
    priority = _PRIORITY_ALIASES.get(str(source.get("priority") or ""), str(source.get("priority") or "中"))
    if priority not in PLAN_PRIORITIES:
        priority = "中"
    raw_tasks = source.get("tasks") if isinstance(source.get("tasks"), list) else []
    tasks: list[dict[str, Any]] = []
    for index, raw_task in enumerate(raw_tasks):
        task = deepcopy(raw_task) if isinstance(raw_task, dict) else {}
        task["id"] = str(task.get("id") or f"{plan_id or 'plan'}-task-{index + 1}")
        task["title"] = str(task.get("title") or "")
        task["scheduled_date"] = str(task.get("scheduled_date") or task.get("scheduledDate") or task.get("date") or "")
        task["done"] = bool(task.get("done"))
        task["note"] = str(task.get("note") or "")
        tasks.append(task)
    tags_value = source.get("tags", [])
    tags = [str(item) for item in tags_value if str(item).strip()] if isinstance(tags_value, list) else []
    source.update(
        {
            "schema_version": PLAN_SCHEMA_VERSION,
            "id": plan_id,
            "title": str(source.get("title") or ""),
            "goal": str(source.get("goal") or ""),
            "start_date": str(source.get("start_date") or source.get("startDate") or source.get("date") or ""),
            "due_date": str(source.get("due_date") or source.get("deadline") or ""),
            "status": status,
            "priority": priority,
            "notes": str(source.get("notes") or source.get("note") or ""),
            "tags": tags,
            "tasks": tasks,
            "plan_type": str(source.get("plan_type") or "add"),
            "subtract_mode": str(source.get("subtract_mode") or ""),
            "trigger_scene": str(source.get("trigger_scene") or ""),
            "avoid_behavior": str(source.get("avoid_behavior") or ""),
            "reason": str(source.get("reason") or ""),
            "alternative_action": str(source.get("alternative_action") or ""),
            "created_at": str(source.get("created_at") or ""),
            "updated_at": str(source.get("updated_at") or ""),
            "deleted": bool(source.get("deleted")),
            "deleted_at": str(source.get("deleted_at") or ""),
        }
    )
    return source


def calculate_plan_progress(plan: dict[str, Any]) -> int:
    tasks = plan.get("tasks") if isinstance(plan.get("tasks"), list) else []
    return round(100 * sum(bool(task.get("done")) for task in tasks if isinstance(task, dict)) / len(tasks)) if tasks else 0
