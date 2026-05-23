from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from .models import now_iso


@dataclass(slots=True)
class NoteEntry:
    id: str
    title: str
    description: str
    body: str
    created_at: str
    updated_at: str

    @property
    def display_title(self) -> str:
        return self.title.strip() or "未命名笔记"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "body": self.body,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NoteEntry":
        return cls(
            id=str(data.get("id", "")),
            title=str(data.get("title", "")),
            description=str(data.get("description", "")),
            body=str(data.get("body", "")),
            created_at=str(data.get("created_at", now_iso())),
            updated_at=str(data.get("updated_at", now_iso())),
        )


class NoteStorage:
    def __init__(self, root_dir: Path | str):
        self.root_dir = Path(root_dir)
        self.notes_dir = self.root_dir / "notes"
        self.notes_dir.mkdir(parents=True, exist_ok=True)

    def create_empty_note(self) -> NoteEntry:
        timestamp = now_iso()
        return NoteEntry(
            id=uuid4().hex,
            title="",
            description="",
            body="",
            created_at=timestamp,
            updated_at=timestamp,
        )

    def note_dir(self, note_id: str) -> Path:
        return self.notes_dir / note_id

    def list_notes(self, query: str = "") -> list[NoteEntry]:
        keyword = query.strip().lower()
        items: list[NoteEntry] = []
        for child in self.notes_dir.iterdir():
            if not child.is_dir():
                continue
            try:
                note = self._load_from_dir(child, include_deleted=False)
            except (FileNotFoundError, KeyError, json.JSONDecodeError, OSError, ValueError):
                continue
            if keyword and not self._matches_query(note, keyword):
                continue
            items.append(note)
        items.sort(key=lambda item: item.updated_at, reverse=True)
        return items

    def load_note(self, note_id: str) -> NoteEntry:
        return self._load_from_dir(self.note_dir(note_id), include_deleted=True)

    def save_note(self, note: NoteEntry) -> NoteEntry:
        note_dir = self.note_dir(note.id)
        note_dir.mkdir(parents=True, exist_ok=True)
        note.updated_at = now_iso()
        (note_dir / "note.json").write_text(
            json.dumps(note.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.load_note(note.id)

    def delete_note(self, note_id: str) -> None:
        metadata_path = self.note_dir(note_id) / "note.json"
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
        data["deleted"] = True
        data["deleted_at"] = now_iso()
        data["updated_at"] = data["deleted_at"]
        metadata_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_from_dir(self, note_dir: Path, include_deleted: bool) -> NoteEntry:
        data = json.loads((note_dir / "note.json").read_text(encoding="utf-8"))
        if data.get("deleted") and not include_deleted:
            raise ValueError("note deleted")
        return NoteEntry.from_dict(data)

    def _matches_query(self, note: NoteEntry, keyword: str) -> bool:
        haystacks = [
            note.title,
            note.description,
            note.body,
        ]
        return any(keyword in text.lower() for text in haystacks if text)
