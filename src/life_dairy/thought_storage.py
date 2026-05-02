from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from .models import now_iso


THOUGHT_TYPES = [
    "接单思考",
    "学习思考",
    "人生方向",
    "关系问题",
    "情绪问题",
    "项目方案",
    "消费决策",
    "身体作息",
    "其他",
]
THOUGHT_STATUSES = ["思考中", "已有结论", "已转计划", "暂时搁置"]


@dataclass(slots=True)
class ThoughtEntry:
    id: str
    title: str
    description: str
    thought_type: str
    status: str
    created_at: str
    updated_at: str
    ideas: list[dict[str, Any]] = field(default_factory=list)
    preliminary_conclusion: str = ""
    notes: str = ""
    related_diaries: list[dict[str, Any]] = field(default_factory=list)
    related_resources: list[dict[str, Any]] = field(default_factory=list)
    related_self_analysis: list[dict[str, Any]] = field(default_factory=list)

    @property
    def display_title(self) -> str:
        return self.title.strip() or "未命名思考"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "type": self.thought_type,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "ideas": self.ideas,
            "preliminary_conclusion": self.preliminary_conclusion,
            "notes": self.notes,
            "related_diaries": self.related_diaries,
            "related_resources": self.related_resources,
            "related_self_analysis": self.related_self_analysis,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ThoughtEntry":
        return cls(
            id=str(data.get("id", "")),
            title=str(data.get("title", "")),
            description=str(data.get("description", "")),
            thought_type=str(data.get("type", "其他")),
            status=str(data.get("status", "思考中")),
            created_at=str(data.get("created_at", now_iso())),
            updated_at=str(data.get("updated_at", now_iso())),
            ideas=[item for item in data.get("ideas", []) if isinstance(item, dict)],
            preliminary_conclusion=str(data.get("preliminary_conclusion", "")),
            notes=str(data.get("notes", "")),
            related_diaries=[item for item in data.get("related_diaries", []) if isinstance(item, dict)],
            related_resources=[item for item in data.get("related_resources", []) if isinstance(item, dict)],
            related_self_analysis=[item for item in data.get("related_self_analysis", []) if isinstance(item, dict)],
        )


class ThoughtStorage:
    def __init__(self, root_dir: Path | str):
        self.root_dir = Path(root_dir)
        self.thoughts_dir = self.root_dir / "thoughts"
        self.thoughts_dir.mkdir(parents=True, exist_ok=True)

    def create_empty_thought(self) -> ThoughtEntry:
        timestamp = now_iso()
        return ThoughtEntry(
            id=uuid4().hex,
            title="",
            description="",
            thought_type="其他",
            status="思考中",
            created_at=timestamp,
            updated_at=timestamp,
        )

    def thought_dir(self, thought_id: str) -> Path:
        return self.thoughts_dir / thought_id

    def list_thoughts(self, query: str = "", thought_type: str = "全部", status: str = "全部") -> list[ThoughtEntry]:
        keyword = query.strip().lower()
        items: list[ThoughtEntry] = []
        for child in self.thoughts_dir.iterdir():
            if not child.is_dir():
                continue
            try:
                thought = self._load_from_dir(child, include_deleted=False)
            except (FileNotFoundError, KeyError, json.JSONDecodeError, OSError, ValueError):
                continue
            if thought_type != "全部" and thought.thought_type != thought_type:
                continue
            if status != "全部" and thought.status != status:
                continue
            if keyword and not self._matches_query(thought, keyword):
                continue
            items.append(thought)
        items.sort(key=lambda item: (item.updated_at, item.created_at), reverse=True)
        return items

    def load_thought(self, thought_id: str) -> ThoughtEntry:
        return self._load_from_dir(self.thought_dir(thought_id), include_deleted=True)

    def save_thought(self, thought: ThoughtEntry) -> ThoughtEntry:
        thought_dir = self.thought_dir(thought.id)
        thought_dir.mkdir(parents=True, exist_ok=True)
        thought.updated_at = now_iso()
        if thought.thought_type not in THOUGHT_TYPES:
            thought.thought_type = "其他"
        if thought.status not in THOUGHT_STATUSES:
            thought.status = "思考中"
        (thought_dir / "thought.json").write_text(
            json.dumps(thought.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.load_thought(thought.id)

    def delete_thought(self, thought_id: str) -> None:
        metadata_path = self.thought_dir(thought_id) / "thought.json"
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
        data["deleted"] = True
        data["deleted_at"] = now_iso()
        data["updated_at"] = data["deleted_at"]
        metadata_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_from_dir(self, thought_dir: Path, include_deleted: bool) -> ThoughtEntry:
        data = json.loads((thought_dir / "thought.json").read_text(encoding="utf-8"))
        if data.get("deleted") and not include_deleted:
            raise ValueError("thought deleted")
        return ThoughtEntry.from_dict(data)

    def _matches_query(self, thought: ThoughtEntry, keyword: str) -> bool:
        idea_text = " ".join(str(item.get("text", "")) for item in thought.ideas)
        haystacks = [
            thought.title,
            thought.description,
            thought.thought_type,
            thought.status,
            idea_text,
            thought.preliminary_conclusion,
            thought.notes,
        ]
        return any(keyword in text.lower() for text in haystacks if text)
