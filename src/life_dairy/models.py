from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="microseconds")


@dataclass(slots=True)
class DiaryImage:
    file_name: str
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_name": self.file_name,
            "label": self.label,
        }

    @classmethod
    def from_value(cls, value: Any) -> "DiaryImage":
        if isinstance(value, str):
            return cls(file_name=value, label="")
        if isinstance(value, dict):
            return cls(
                file_name=str(value.get("file_name", "")),
                label=str(value.get("label", "")),
            )
        raise ValueError("invalid image metadata")


@dataclass(slots=True)
class DiaryImageDraft:
    source_path: Path
    label: str = ""


@dataclass(slots=True)
class DiaryEntry:
    id: str
    date: str
    title: str
    body: str
    created_at: str
    updated_at: str
    images: list[DiaryImage] = field(default_factory=list)

    @property
    def display_title(self) -> str:
        return self.title.strip() or "无标题日记"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "date": self.date,
            "title": self.title,
            "images": [item.to_dict() for item in self.images],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "body_file": "content.md",
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], body: str) -> "DiaryEntry":
        return cls(
            id=str(data["id"]),
            date=str(data.get("date", "")),
            title=str(data.get("title", "")),
            body=body,
            created_at=str(data.get("created_at", now_iso())),
            updated_at=str(data.get("updated_at", now_iso())),
            images=[DiaryImage.from_value(item) for item in data.get("images", [])],
        )


@dataclass(slots=True)
class FootprintImage:
    file_name: str
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_name": self.file_name,
            "label": self.label,
        }

    @classmethod
    def from_value(cls, value: Any) -> "FootprintImage":
        if isinstance(value, str):
            return cls(file_name=value, label="")
        if isinstance(value, dict):
            return cls(
                file_name=str(value.get("file_name", "")),
                label=str(value.get("label", "")),
            )
        raise ValueError("invalid footprint image metadata")


@dataclass(slots=True)
class FootprintImageDraft:
    source_path: Path
    label: str = ""


@dataclass(slots=True)
class FootprintVisit:
    id: str
    date: str
    thought: str
    created_at: str
    updated_at: str
    related_entry_id: str = ""
    images: list[FootprintImage] = field(default_factory=list)

    @property
    def display_title(self) -> str:
        return self.date.strip() or "未设日期关联"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "date": self.date,
            "images": [item.to_dict() for item in self.images],
            "related_entry_id": self.related_entry_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "thought_file": "thought.md",
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], thought: str) -> "FootprintVisit":
        return cls(
            id=str(data["id"]),
            date=str(data.get("date", "")),
            thought=thought,
            created_at=str(data.get("created_at", now_iso())),
            updated_at=str(data.get("updated_at", now_iso())),
            related_entry_id=str(data.get("related_entry_id", "")),
            images=[FootprintImage.from_value(item) for item in data.get("images", [])],
        )


@dataclass(slots=True)
class FootprintPlace:
    id: str
    place_name: str
    summary: str
    created_at: str
    updated_at: str
    images: list[FootprintImage] = field(default_factory=list)
    visits: list[FootprintVisit] = field(default_factory=list)

    @property
    def display_title(self) -> str:
        return self.place_name.strip() or "未命名地点"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "place_name": self.place_name,
            "images": [item.to_dict() for item in self.images],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "summary_file": "summary.md",
            "visit_ids": [visit.id for visit in self.visits],
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        summary: str,
        visits: list[FootprintVisit],
    ) -> "FootprintPlace":
        return cls(
            id=str(data["id"]),
            place_name=str(data.get("place_name", "")),
            summary=summary,
            created_at=str(data.get("created_at", now_iso())),
            updated_at=str(data.get("updated_at", now_iso())),
            images=[FootprintImage.from_value(item) for item in data.get("images", [])],
            visits=visits,
        )


@dataclass(slots=True)
class BookImage:
    file_name: str
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_name": self.file_name,
            "label": self.label,
        }

    @classmethod
    def from_value(cls, value: Any) -> "BookImage":
        if isinstance(value, str):
            return cls(file_name=value, label="")
        if isinstance(value, dict):
            return cls(
                file_name=str(value.get("file_name", "")),
                label=str(value.get("label", "")),
            )
        raise ValueError("invalid book image metadata")


@dataclass(slots=True)
class BookImageDraft:
    source_path: Path
    label: str = ""


@dataclass(slots=True)
class BookRelatedDiary:
    entry_id: str
    date: str
    title: str

    @property
    def display_title(self) -> str:
        title = self.title.strip() or "无标题日记"
        return f"{self.date} | {title}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "date": self.date,
            "title": self.title,
        }

    @classmethod
    def from_value(cls, value: Any) -> "BookRelatedDiary":
        if isinstance(value, dict):
            return cls(
                entry_id=str(value.get("entry_id", "")),
                date=str(value.get("date", "")),
                title=str(value.get("title", "")),
            )
        raise ValueError("invalid related diary metadata")


@dataclass(slots=True)
class BookEntry:
    id: str
    title: str
    author: str
    status: str
    start_date: str
    finish_date: str
    tags: list[str]
    summary: str
    notes: str
    created_at: str
    updated_at: str
    images: list[BookImage] = field(default_factory=list)
    related_diaries: list[BookRelatedDiary] = field(default_factory=list)

    @property
    def display_title(self) -> str:
        return self.title.strip() or "未命名书籍"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "status": self.status,
            "start_date": self.start_date,
            "finish_date": self.finish_date,
            "tags": self.tags,
            "images": [item.to_dict() for item in self.images],
            "related_diaries": [item.to_dict() for item in self.related_diaries],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "summary_file": "summary.md",
            "notes_file": "notes.md",
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], summary: str, notes: str) -> "BookEntry":
        raw_tags = data.get("tags", [])
        tags = [str(item).strip() for item in raw_tags if str(item).strip()]
        return cls(
            id=str(data["id"]),
            title=str(data.get("title", "")),
            author=str(data.get("author", "")),
            status=str(data.get("status", "想读")),
            start_date=str(data.get("start_date", "")),
            finish_date=str(data.get("finish_date", "")),
            tags=tags,
            summary=summary,
            notes=notes,
            created_at=str(data.get("created_at", now_iso())),
            updated_at=str(data.get("updated_at", now_iso())),
            images=[BookImage.from_value(item) for item in data.get("images", [])],
            related_diaries=[BookRelatedDiary.from_value(item) for item in data.get("related_diaries", [])],
        )


@dataclass(slots=True)
class PlanItem:
    id: str
    title: str
    due_date: str
    status: str
    priority: str
    notes: str
    created_at: str
    updated_at: str

    @property
    def display_title(self) -> str:
        return self.title.strip() or "未命名计划"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "due_date": self.due_date,
            "status": self.status,
            "priority": self.priority,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlanItem":
        return cls(
            id=str(data["id"]),
            title=str(data.get("title", "")),
            due_date=str(data.get("due_date", "")),
            status=str(data.get("status", "未开始")),
            priority=str(data.get("priority", "普通")),
            notes=str(data.get("notes", "")),
            created_at=str(data.get("created_at", now_iso())),
            updated_at=str(data.get("updated_at", now_iso())),
        )
