from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from .models import now_iso


RESOURCE_TYPES = ["接单", "学习", "武术", "精神分析", "消费", "项目", "关系", "身体", "其他"]
RESOURCE_STATUSES = ["考虑中", "已决定", "已放弃", "已完成"]
RESOURCE_ITEM_TYPES = ["时间", "金钱", "精力", "情绪", "勇气", "身体", "注意力", "风险", "机会成本", "其他"]
TIME_BLOCK_OPTIONS = ["不打断", "轻微打断", "明显打断", "毁掉半天", "毁掉一天"]
MONEY_CYCLES = ["一次性", "每天", "每周", "每月", "每年"]
MONEY_DIRECTIONS = ["收入", "支出", "需要预留"]


@dataclass(slots=True)
class ResourceEntry:
    id: str
    title: str
    description: str
    resource_type: str
    status: str
    created_at: str
    updated_at: str
    resource_items: list[dict[str, Any]] = field(default_factory=list)
    overall_judgement: str = ""
    subjective_feeling: str = ""
    recurrence_test: dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    related_diaries: list[dict[str, Any]] = field(default_factory=list)
    related_thoughts: list[dict[str, Any]] = field(default_factory=list)
    related_self_analysis: list[dict[str, Any]] = field(default_factory=list)

    @property
    def display_title(self) -> str:
        return self.title.strip() or "未命名资源评估"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "type": self.resource_type,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "resource_items": self.resource_items,
            "overall_judgement": self.overall_judgement,
            "subjective_feeling": self.subjective_feeling,
            "recurrence_test": self.recurrence_test,
            "notes": self.notes,
            "related_diaries": self.related_diaries,
            "related_thoughts": self.related_thoughts,
            "related_self_analysis": self.related_self_analysis,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResourceEntry":
        recurrence_test = data.get("recurrence_test", {})
        if not isinstance(recurrence_test, dict):
            recurrence_test = {}
        return cls(
            id=str(data.get("id", "")),
            title=str(data.get("title", "")),
            description=str(data.get("description", "")),
            resource_type=str(data.get("type", "其他")),
            status=str(data.get("status", "考虑中")),
            created_at=str(data.get("created_at", now_iso())),
            updated_at=str(data.get("updated_at", now_iso())),
            resource_items=[item for item in data.get("resource_items", []) if isinstance(item, dict)],
            overall_judgement=str(data.get("overall_judgement", "")),
            subjective_feeling=str(data.get("subjective_feeling", "")),
            recurrence_test=recurrence_test,
            notes=str(data.get("notes", "")),
            related_diaries=[item for item in data.get("related_diaries", []) if isinstance(item, dict)],
            related_thoughts=[item for item in data.get("related_thoughts", []) if isinstance(item, dict)],
            related_self_analysis=[item for item in data.get("related_self_analysis", []) if isinstance(item, dict)],
        )


class ResourceStorage:
    def __init__(self, root_dir: Path | str):
        self.root_dir = Path(root_dir)
        self.resources_dir = self.root_dir / "resources"
        self.resources_dir.mkdir(parents=True, exist_ok=True)

    def create_empty_resource(self) -> ResourceEntry:
        timestamp = now_iso()
        return ResourceEntry(
            id=uuid4().hex,
            title="",
            description="",
            resource_type="其他",
            status="考虑中",
            created_at=timestamp,
            updated_at=timestamp,
            recurrence_test={
                "next_week": "",
                "one_year": "",
                "repeat_willingness": "",
            },
        )

    def resource_dir(self, resource_id: str) -> Path:
        return self.resources_dir / resource_id

    def list_resources(self, query: str = "", resource_type: str = "全部", status: str = "全部") -> list[ResourceEntry]:
        keyword = query.strip().lower()
        items: list[ResourceEntry] = []
        for child in self.resources_dir.iterdir():
            if not child.is_dir():
                continue
            try:
                resource = self._load_from_dir(child, include_deleted=False)
            except (FileNotFoundError, KeyError, json.JSONDecodeError, OSError, ValueError):
                continue
            if resource_type != "全部" and resource.resource_type != resource_type:
                continue
            if status != "全部" and resource.status != status:
                continue
            if keyword and not self._matches_query(resource, keyword):
                continue
            items.append(resource)
        items.sort(key=lambda item: (item.updated_at, item.created_at), reverse=True)
        return items

    def load_resource(self, resource_id: str) -> ResourceEntry:
        return self._load_from_dir(self.resource_dir(resource_id), include_deleted=True)

    def save_resource(self, resource: ResourceEntry) -> ResourceEntry:
        resource_dir = self.resource_dir(resource.id)
        resource_dir.mkdir(parents=True, exist_ok=True)
        resource.updated_at = now_iso()
        if resource.resource_type not in RESOURCE_TYPES:
            resource.resource_type = "其他"
        if resource.status not in RESOURCE_STATUSES:
            resource.status = "考虑中"
        (resource_dir / "resource.json").write_text(
            json.dumps(resource.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.load_resource(resource.id)

    def delete_resource(self, resource_id: str) -> None:
        metadata_path = self.resource_dir(resource_id) / "resource.json"
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
        data["deleted"] = True
        data["deleted_at"] = now_iso()
        data["updated_at"] = data["deleted_at"]
        metadata_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_from_dir(self, resource_dir: Path, include_deleted: bool) -> ResourceEntry:
        data = json.loads((resource_dir / "resource.json").read_text(encoding="utf-8"))
        if data.get("deleted") and not include_deleted:
            raise ValueError("resource deleted")
        return ResourceEntry.from_dict(data)

    def _matches_query(self, resource: ResourceEntry, keyword: str) -> bool:
        item_text = " ".join(json.dumps(item, ensure_ascii=False) for item in resource.resource_items)
        test_text = json.dumps(resource.recurrence_test, ensure_ascii=False)
        haystacks = [
            resource.title,
            resource.description,
            resource.resource_type,
            resource.status,
            item_text,
            resource.overall_judgement,
            resource.subjective_feeling,
            test_text,
            resource.notes,
        ]
        return any(keyword in text.lower() for text in haystacks if text)
