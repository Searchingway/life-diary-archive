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
class LessonImage:
    file_name: str
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_name": self.file_name,
            "label": self.label,
        }

    @classmethod
    def from_value(cls, value: Any) -> "LessonImage":
        if isinstance(value, str):
            return cls(file_name=value, label="")
        if isinstance(value, dict):
            return cls(
                file_name=str(value.get("file_name", "")),
                label=str(value.get("label", "")),
            )
        raise ValueError("invalid lesson image metadata")


@dataclass(slots=True)
class LessonImageDraft:
    source_path: Path
    label: str = ""


@dataclass(slots=True)
class LessonRelatedDiary:
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
    def from_value(cls, value: Any) -> "LessonRelatedDiary":
        if isinstance(value, dict):
            return cls(
                entry_id=str(value.get("entry_id", "")),
                date=str(value.get("date", "")),
                title=str(value.get("title", "")),
            )
        raise ValueError("invalid lesson related diary metadata")


@dataclass(slots=True)
class LessonEntry:
    id: str
    title: str
    date: str
    category: str
    severity: str
    tags: list[str]
    event: str
    judgment: str
    result: str
    mistake: str
    root_cause: str
    cost: str
    next_action: str
    one_sentence: str
    created_at: str
    updated_at: str
    images: list[LessonImage] = field(default_factory=list)
    related_diaries: list[LessonRelatedDiary] = field(default_factory=list)

    @property
    def display_title(self) -> str:
        return self.title.strip() or "未命名反思"

    def to_dict(self) -> dict[str, Any]:
        return {
            "lesson_id": self.id,
            "title": self.title,
            "date": self.date,
            "category": self.category,
            "severity": self.severity,
            "tags": self.tags,
            "images": [item.to_dict() for item in self.images],
            "related_entries": [item.to_dict() for item in self.related_diaries],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted": False,
            "content_file": "content.md",
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], sections: dict[str, str]) -> "LessonEntry":
        raw_tags = data.get("tags", [])
        tags = [str(item).strip() for item in raw_tags if str(item).strip()]
        lesson_id = str(data.get("lesson_id") or data.get("id"))
        return cls(
            id=lesson_id,
            title=str(data.get("title", "")),
            date=str(data.get("date", "")),
            category=str(data.get("category", "其他")),
            severity=str(data.get("severity", "中等")),
            tags=tags,
            event=sections.get("事件经过", ""),
            judgment=sections.get("当时我是怎么判断的", ""),
            result=sections.get("结果是什么", ""),
            mistake=sections.get("我哪里判断错了", ""),
            root_cause=sections.get("真正的问题是什么", ""),
            cost=sections.get("这次的代价", ""),
            next_action=sections.get("下次遇到类似情况要怎么做", ""),
            one_sentence=sections.get("一句话教训", ""),
            created_at=str(data.get("created_at", now_iso())),
            updated_at=str(data.get("updated_at", now_iso())),
            images=[LessonImage.from_value(item) for item in data.get("images", [])],
            related_diaries=[LessonRelatedDiary.from_value(item) for item in data.get("related_entries", [])],
        )


@dataclass(slots=True)
class SelfAnalysisImage:
    file_name: str
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_name": self.file_name,
            "label": self.label,
        }

    @classmethod
    def from_value(cls, value: Any) -> "SelfAnalysisImage":
        if isinstance(value, str):
            return cls(file_name=value, label="")
        if isinstance(value, dict):
            return cls(
                file_name=str(value.get("file_name", "")),
                label=str(value.get("label", "")),
            )
        raise ValueError("invalid self analysis image metadata")


@dataclass(slots=True)
class SelfAnalysisImageDraft:
    source_path: Path
    label: str = ""


@dataclass(slots=True)
class SelfAnalysisRelatedDiary:
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
    def from_value(cls, value: Any) -> "SelfAnalysisRelatedDiary":
        if isinstance(value, dict):
            return cls(
                entry_id=str(value.get("entry_id", "")),
                date=str(value.get("date", "")),
                title=str(value.get("title", "")),
            )
        raise ValueError("invalid self analysis related diary metadata")


@dataclass(slots=True)
class SelfAnalysisRelatedLesson:
    lesson_id: str
    date: str
    title: str

    @property
    def display_title(self) -> str:
        title = self.title.strip() or "未命名反思"
        return f"{self.date} | {title}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "lesson_id": self.lesson_id,
            "date": self.date,
            "title": self.title,
        }

    @classmethod
    def from_value(cls, value: Any) -> "SelfAnalysisRelatedLesson":
        if isinstance(value, dict):
            return cls(
                lesson_id=str(value.get("lesson_id", "")),
                date=str(value.get("date", "")),
                title=str(value.get("title", "")),
            )
        raise ValueError("invalid self analysis related lesson metadata")


@dataclass(slots=True)
class SelfAnalysisEntry:
    id: str
    title: str
    date: str
    analysis_type: str
    tags: list[str]
    trigger_event: str
    emotion: str
    body_reaction: str
    surface_want: str
    real_fear: str
    real_want: str
    repeated_pattern: str
    imagined_judgment: str
    defense: str
    similar_experience: str
    insight: str
    next_action: str
    created_at: str
    updated_at: str
    images: list[SelfAnalysisImage] = field(default_factory=list)
    related_diaries: list[SelfAnalysisRelatedDiary] = field(default_factory=list)
    related_lessons: list[SelfAnalysisRelatedLesson] = field(default_factory=list)

    @property
    def display_title(self) -> str:
        return self.title.strip() or "未命名自我分析"

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_id": self.id,
            "title": self.title,
            "date": self.date,
            "analysis_type": self.analysis_type,
            "tags": self.tags,
            "images": [item.to_dict() for item in self.images],
            "related_entries": [item.to_dict() for item in self.related_diaries],
            "related_lessons": [item.to_dict() for item in self.related_lessons],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted": False,
            "content_file": "content.md",
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], sections: dict[str, str]) -> "SelfAnalysisEntry":
        raw_tags = data.get("tags", [])
        tags = [str(item).strip() for item in raw_tags if str(item).strip()]
        analysis_id = str(data.get("analysis_id") or data.get("id"))
        return cls(
            id=analysis_id,
            title=str(data.get("title", "")),
            date=str(data.get("date", "")),
            analysis_type=str(data.get("analysis_type", "其他")),
            tags=tags,
            trigger_event=sections.get("触发事件", ""),
            emotion=sections.get("当时的情绪", ""),
            body_reaction=sections.get("当时的身体反应", ""),
            surface_want=sections.get("我表面上想要什么", ""),
            real_fear=sections.get("我真正害怕什么", ""),
            real_want=sections.get("我真正想要什么", ""),
            repeated_pattern=sections.get("我在重复什么模式", ""),
            imagined_judgment=sections.get("我想象中的别人怎么看我", ""),
            defense=sections.get("我采取了什么防御方式", ""),
            similar_experience=sections.get("这件事和过去哪些经历相似", ""),
            insight=sections.get("我从中看见了什么", ""),
            next_action=sections.get("下一步我可以怎么做", ""),
            created_at=str(data.get("created_at", now_iso())),
            updated_at=str(data.get("updated_at", now_iso())),
            images=[SelfAnalysisImage.from_value(item) for item in data.get("images", [])],
            related_diaries=[
                SelfAnalysisRelatedDiary.from_value(item)
                for item in data.get("related_entries", [])
            ],
            related_lessons=[
                SelfAnalysisRelatedLesson.from_value(item)
                for item in data.get("related_lessons", [])
            ],
        )


@dataclass(slots=True)
class WorkImage:
    file_name: str
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_name": self.file_name,
            "label": self.label,
        }

    @classmethod
    def from_value(cls, value: Any) -> "WorkImage":
        if isinstance(value, str):
            return cls(file_name=value, label="")
        if isinstance(value, dict):
            return cls(
                file_name=str(value.get("file_name", "")),
                label=str(value.get("label", "")),
            )
        raise ValueError("invalid work image metadata")


@dataclass(slots=True)
class WorkImageDraft:
    source_path: Path
    label: str = ""


@dataclass(slots=True)
class WorkRelatedDiary:
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
    def from_value(cls, value: Any) -> "WorkRelatedDiary":
        if isinstance(value, dict):
            return cls(
                entry_id=str(value.get("entry_id", "")),
                date=str(value.get("date", "")),
                title=str(value.get("title", "")),
            )
        raise ValueError("invalid work related diary metadata")


@dataclass(slots=True)
class WorkRelatedSelfAnalysis:
    analysis_id: str
    date: str
    title: str

    @property
    def display_title(self) -> str:
        title = self.title.strip() or "未命名自我分析"
        return f"{self.date} | {title}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "date": self.date,
            "title": self.title,
        }

    @classmethod
    def from_value(cls, value: Any) -> "WorkRelatedSelfAnalysis":
        if isinstance(value, dict):
            return cls(
                analysis_id=str(value.get("analysis_id", "")),
                date=str(value.get("date", "")),
                title=str(value.get("title", "")),
            )
        raise ValueError("invalid work related self analysis metadata")


@dataclass(slots=True)
class WorkEntry:
    id: str
    title: str
    work_type: str
    creator: str
    status: str
    start_date: str
    finish_date: str
    rating: str
    tags: list[str]
    one_sentence: str
    summary: str
    liked: str
    disliked: str
    touched: str
    favorite_parts: str
    self_connection: str
    past_connection: str
    final_review: str
    created_at: str
    updated_at: str
    images: list[WorkImage] = field(default_factory=list)
    related_diaries: list[WorkRelatedDiary] = field(default_factory=list)
    related_self_analysis: list[WorkRelatedSelfAnalysis] = field(default_factory=list)

    @property
    def display_title(self) -> str:
        return self.title.strip() or "未命名作品"

    def to_dict(self) -> dict[str, Any]:
        return {
            "work_id": self.id,
            "title": self.title,
            "work_type": self.work_type,
            "creator": self.creator,
            "status": self.status,
            "start_date": self.start_date,
            "finish_date": self.finish_date,
            "rating": self.rating,
            "tags": self.tags,
            "images": [item.to_dict() for item in self.images],
            "related_entries": [item.to_dict() for item in self.related_diaries],
            "related_self_analysis": [item.to_dict() for item in self.related_self_analysis],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted": False,
            "content_file": "content.md",
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], sections: dict[str, str]) -> "WorkEntry":
        raw_tags = data.get("tags", [])
        tags = [str(item).strip() for item in raw_tags if str(item).strip()]
        work_id = str(data.get("work_id") or data.get("id"))
        return cls(
            id=work_id,
            title=str(data.get("title", "")),
            work_type=str(data.get("work_type", "其他")),
            creator=str(data.get("creator", "")),
            status=str(data.get("status", "想看")),
            start_date=str(data.get("start_date", "")),
            finish_date=str(data.get("finish_date", "")),
            rating=str(data.get("rating", "")),
            tags=tags,
            one_sentence=sections.get("一句话印象", ""),
            summary=sections.get("内容摘要", ""),
            liked=sections.get("我喜欢的地方", ""),
            disliked=sections.get("我不喜欢的地方", ""),
            touched=sections.get("触动我的地方", ""),
            favorite_parts=sections.get("喜欢的角色 / 场景 / 台词", ""),
            self_connection=sections.get("让我想到的自己", ""),
            past_connection=sections.get("和我过去经历的关联", ""),
            final_review=sections.get("我的最终评价", ""),
            created_at=str(data.get("created_at", now_iso())),
            updated_at=str(data.get("updated_at", now_iso())),
            images=[WorkImage.from_value(item) for item in data.get("images", [])],
            related_diaries=[
                WorkRelatedDiary.from_value(item)
                for item in data.get("related_entries", [])
            ],
            related_self_analysis=[
                WorkRelatedSelfAnalysis.from_value(item)
                for item in data.get("related_self_analysis", [])
            ],
        )


@dataclass(slots=True)
class PlanItem:
    id: str
    title: str
    due_date: str
    status: str
    priority: str
    notes: str
    tags: list[str]
    plan_type: str
    subtract_mode: str
    trigger_scene: str
    avoid_behavior: str
    reason: str
    alternative_action: str
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
            "tags": self.tags,
            "plan_type": self.plan_type,
            "subtract_mode": self.subtract_mode,
            "trigger_scene": self.trigger_scene,
            "avoid_behavior": self.avoid_behavior,
            "reason": self.reason,
            "alternative_action": self.alternative_action,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlanItem":
        raw_tags = data.get("tags", [])
        if isinstance(raw_tags, str):
            raw_tags = raw_tags.replace("，", ",").split(",")
        tags = [str(item).strip() for item in raw_tags if str(item).strip()]
        plan_type = str(data.get("plan_type", "add"))
        if plan_type not in {"add", "subtract"}:
            plan_type = "add"
        return cls(
            id=str(data["id"]),
            title=str(data.get("title", "")),
            due_date=str(data.get("due_date", "")),
            status=str(data.get("status", "未开始")),
            priority=str(data.get("priority", "普通")),
            notes=str(data.get("notes", "")),
            tags=tags,
            plan_type=plan_type,
            subtract_mode=str(data.get("subtract_mode", "")),
            trigger_scene=str(data.get("trigger_scene", "")),
            avoid_behavior=str(data.get("avoid_behavior", "")),
            reason=str(data.get("reason", "")),
            alternative_action=str(data.get("alternative_action", "")),
            created_at=str(data.get("created_at", now_iso())),
            updated_at=str(data.get("updated_at", now_iso())),
        )
