from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from .models import now_iso


INFO_MEMO_TYPES = ["接单记录", "网课资源", "通用信息"]

ORDER_STATUSES = ["沟通中", "已接单", "进行中", "待验收", "已交付", "已结款", "已取消"]
COURSE_STATUSES = ["想看", "已收藏", "学习中", "暂停", "已学完", "放弃"]
GENERAL_STATUSES = ["未处理", "已记录", "处理中", "已完成", "已归档"]

PRIORITIES = ["低", "中", "高"]
DIRECTIONS = ["AI 编程", "Python", "Qt", "前端", "小程序", "机械专业", "考研", "哲学", "其他"]
GENERAL_CATEGORIES = ["软件", "网站", "工具", "账号信息", "客户信息", "学习资料", "想法线索", "其他"]

STATUS_MAP: dict[str, list[str]] = {
    "接单记录": ORDER_STATUSES,
    "网课资源": COURSE_STATUSES,
    "通用信息": GENERAL_STATUSES,
}

ALL_STATUSES: list[str] = []
_seen: set[str] = set()
for s_list in STATUS_MAP.values():
    for s in s_list:
        if s not in _seen:
            _seen.add(s)
            ALL_STATUSES.append(s)


DEFAULT_STATUS: dict[str, str] = {
    "接单记录": "沟通中",
    "网课资源": "想看",
    "通用信息": "未处理",
}


def _parse_amount(text: str) -> float:
    """Parse a user-entered amount string to float.

    Returns 0.0 for empty or invalid input.
    """
    text = text.strip().replace("¥", "").replace("￥", "").replace(",", "").replace("，", "")
    if not text:
        return 0.0
    try:
        return round(float(text), 2)
    except (ValueError, TypeError):
        return 0.0


def default_type_fields(info_type: str) -> dict[str, Any]:
    if info_type == "接单记录":
        return {
            "customer": "",
            "intermediary": "",
            "executor": "",
            "order_date": "",
            "deadline": "",
            "duration_days": 0,
            "price": 0.0,
            "deposit": 0.0,
            "final_payment": 0.0,
            "deliverables": "",
        }
    if info_type == "网课资源":
        return {
            "course_name": "",
            "platform": "",
            "course_url": "",
            "direction": "",
            "paid_status": "",
            "progress": "",
            "reason": "",
        }
    return {
        "category": "",
        "content": "",
        "reminder_date": "",
    }


@dataclass(slots=True)
class InfoMemoEntry:
    id: str
    title: str
    info_type: str
    status: str
    priority: str
    tags: str
    source: str
    link: str
    local_path: str
    note: str
    created_at: str
    updated_at: str
    type_fields: dict[str, Any] = field(default_factory=dict)

    @property
    def display_title(self) -> str:
        return self.title.strip() or "未命名信息"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "info_type": self.info_type,
            "status": self.status,
            "priority": self.priority,
            "tags": self.tags,
            "source": self.source,
            "link": self.link,
            "local_path": self.local_path,
            "note": self.note,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "type_fields": self.type_fields,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InfoMemoEntry":
        info_type = str(data.get("info_type", "通用信息"))
        tf = data.get("type_fields", {})
        if not isinstance(tf, dict):
            tf = {}
        return cls(
            id=str(data.get("id", "")),
            title=str(data.get("title", "")),
            info_type=info_type,
            status=str(data.get("status", DEFAULT_STATUS.get(info_type, "未处理"))),
            priority=str(data.get("priority", "中")),
            tags=str(data.get("tags", "")),
            source=str(data.get("source", "")),
            link=str(data.get("link", "")),
            local_path=str(data.get("local_path", "")),
            note=str(data.get("note", "")),
            created_at=str(data.get("created_at", now_iso())),
            updated_at=str(data.get("updated_at", now_iso())),
            type_fields={**default_type_fields(info_type), **tf},
        )


class InfoMemoStorage:
    def __init__(self, root_dir: Path | str):
        self.root_dir = Path(root_dir)
        self.info_memos_dir = self.root_dir / "info_memos"
        self.info_memos_dir.mkdir(parents=True, exist_ok=True)

    def create_empty_memo(self) -> InfoMemoEntry:
        timestamp = now_iso()
        return InfoMemoEntry(
            id=uuid4().hex,
            title="",
            info_type="通用信息",
            status="未处理",
            priority="中",
            tags="",
            source="",
            link="",
            local_path="",
            note="",
            created_at=timestamp,
            updated_at=timestamp,
            type_fields=default_type_fields("通用信息"),
        )

    def memo_dir(self, memo_id: str) -> Path:
        return self.info_memos_dir / memo_id

    def list_info_memos(
        self, query: str = "", info_type: str = "全部", status: str = "全部"
    ) -> list[InfoMemoEntry]:
        keyword = query.strip().lower()
        items: list[InfoMemoEntry] = []
        for child in self.info_memos_dir.iterdir():
            if not child.is_dir():
                continue
            try:
                memo = self._load_from_dir(child, include_deleted=False)
            except (FileNotFoundError, KeyError, json.JSONDecodeError, OSError, ValueError):
                continue
            if info_type != "全部" and memo.info_type != info_type:
                continue
            if status != "全部" and memo.status != status:
                continue
            if keyword and not self._matches_query(memo, keyword):
                continue
            items.append(memo)
        items.sort(key=lambda item: (item.updated_at, item.created_at), reverse=True)
        return items

    def load_memo(self, memo_id: str) -> InfoMemoEntry:
        return self._load_from_dir(self.memo_dir(memo_id), include_deleted=True)

    def save_memo(self, memo: InfoMemoEntry) -> InfoMemoEntry:
        memo_dir = self.memo_dir(memo.id)
        memo_dir.mkdir(parents=True, exist_ok=True)
        memo.updated_at = now_iso()
        if memo.info_type not in INFO_MEMO_TYPES:
            memo.info_type = "通用信息"
        expected = STATUS_MAP.get(memo.info_type, GENERAL_STATUSES)
        if memo.status not in expected:
            memo.status = DEFAULT_STATUS.get(memo.info_type, "未处理")
        if memo.priority not in PRIORITIES:
            memo.priority = "中"
        (memo_dir / "info_memo.json").write_text(
            json.dumps(memo.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.load_memo(memo.id)

    def delete_memo(self, memo_id: str) -> None:
        metadata_path = self.memo_dir(memo_id) / "info_memo.json"
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
        data["deleted"] = True
        data["deleted_at"] = now_iso()
        data["updated_at"] = data["deleted_at"]
        metadata_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_from_dir(self, memo_dir: Path, include_deleted: bool) -> InfoMemoEntry:
        data = json.loads((memo_dir / "info_memo.json").read_text(encoding="utf-8"))
        if data.get("deleted") and not include_deleted:
            raise ValueError("memo deleted")
        return InfoMemoEntry.from_dict(data)

    def _matches_query(self, memo: InfoMemoEntry, keyword: str) -> bool:
        tf_text = " ".join(str(v) for v in memo.type_fields.values() if v)
        haystacks = [
            memo.title,
            memo.tags,
            memo.source,
            memo.link,
            memo.note,
            tf_text,
        ]
        return any(keyword in text.lower() for text in haystacks if text)
