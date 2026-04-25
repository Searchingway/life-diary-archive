from __future__ import annotations

import json
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from .models import DiaryEntry, DiaryImage, DiaryImageDraft, now_iso


class DiaryStorage:
    def __init__(self, root_dir: Path | str):
        self.root_dir = Path(root_dir)
        self.entries_dir = self.root_dir / "entries"
        self.entries_dir.mkdir(parents=True, exist_ok=True)

    def create_empty_entry(self) -> DiaryEntry:
        timestamp = now_iso()
        return DiaryEntry(
            id=uuid4().hex,
            date=date.today().isoformat(),
            title="",
            body="",
            created_at=timestamp,
            updated_at=timestamp,
            images=[],
        )

    def entry_dir(self, entry_id: str) -> Path:
        return self.entries_dir / entry_id

    def image_dir(self, entry_id: str) -> Path:
        return self.entry_dir(entry_id) / "images"

    def resolve_image_path(self, entry_id: str, image_name: str) -> Path:
        return self.image_dir(entry_id) / image_name

    def list_entries(self, query: str = "") -> list[DiaryEntry]:
        keyword = query.strip().lower()
        items: list[DiaryEntry] = []
        for child in self.entries_dir.iterdir():
            if not child.is_dir():
                continue
            try:
                entry = self._load_entry_from_directory(child, include_deleted=False)
            except (FileNotFoundError, KeyError, json.JSONDecodeError, OSError, ValueError):
                continue
            if keyword and not self._matches_query(entry, keyword):
                continue
            items.append(entry)

        items.sort(key=lambda entry: (entry.date, entry.updated_at), reverse=True)
        return items

    def list_entries_in_date_range(
        self,
        start_date: str,
        end_date: str,
    ) -> list[DiaryEntry]:
        items = [
            entry
            for entry in self.list_entries()
            if start_date <= entry.date <= end_date
        ]
        items.sort(key=lambda entry: (entry.date, entry.created_at, entry.updated_at))
        return items

    def list_entries_by_date(self, target_date: str) -> list[DiaryEntry]:
        items = [
            entry
            for entry in self.list_entries()
            if entry.date == target_date
        ]
        items.sort(key=lambda entry: (entry.date, entry.created_at, entry.updated_at))
        return items

    def save_entry(
        self,
        entry: DiaryEntry,
        image_items: Iterable[DiaryImageDraft] | None = None,
    ) -> DiaryEntry:
        entry_dir = self.entry_dir(entry.id)
        entry_dir.mkdir(parents=True, exist_ok=True)

        entry.updated_at = now_iso()

        if image_items is not None:
            entry.images = self._sync_images(entry.id, image_items)

        metadata_path = entry_dir / "entry.json"
        content_path = entry_dir / "content.md"

        with metadata_path.open("w", encoding="utf-8") as file:
            json.dump(entry.to_dict(), file, ensure_ascii=False, indent=2)

        content_path.write_text(entry.body, encoding="utf-8")
        return self.load_entry(entry.id)

    def load_entry(self, entry_id: str) -> DiaryEntry:
        return self._load_entry_from_directory(self.entry_dir(entry_id), include_deleted=True)

    def _load_entry_from_directory(self, entry_dir: Path, include_deleted: bool) -> DiaryEntry:
        metadata_path = entry_dir / "entry.json"
        content_path = entry_dir / "content.md"

        with metadata_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if data.get("deleted") and not include_deleted:
            raise ValueError("entry deleted")

        body = ""
        if content_path.exists():
            body = content_path.read_text(encoding="utf-8")

        return DiaryEntry.from_dict(data, body)

    def delete_entry(self, entry_id: str) -> None:
        entry_dir = self.entry_dir(entry_id)
        if not entry_dir.exists():
            raise FileNotFoundError(f"找不到要删除的日记：{entry_id}")
        metadata_path = entry_dir / "entry.json"
        with metadata_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        data["deleted"] = True
        data["deleted_at"] = now_iso()
        data["updated_at"] = now_iso()
        with metadata_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def _matches_query(self, entry: DiaryEntry, keyword: str) -> bool:
        haystacks = [
            entry.date,
            entry.title,
            entry.body,
            " ".join(image.label for image in entry.images if image.label),
        ]
        return any(keyword in text.lower() for text in haystacks if text)

    def _sync_images(
        self,
        entry_id: str,
        image_items: Iterable[DiaryImageDraft],
    ) -> list[DiaryImage]:
        images_dir = self.image_dir(entry_id)
        images_dir.mkdir(parents=True, exist_ok=True)

        keep_images: list[DiaryImage] = []
        keep_lookup: set[str] = set()
        seen_sources: set[str] = set()
        images_root = images_dir.resolve()

        for item in image_items:
            source_path = Path(item.source_path)
            if not source_path.exists():
                raise FileNotFoundError(f"找不到图片文件：{source_path}")

            resolved_source = source_path.resolve()
            source_key = str(resolved_source).lower()
            if source_key in seen_sources:
                continue
            seen_sources.add(source_key)

            if resolved_source.is_relative_to(images_root):
                final_name = resolved_source.name
            else:
                final_name = self._copy_image(images_dir, resolved_source)

            if final_name not in keep_lookup:
                keep_images.append(
                    DiaryImage(
                        file_name=final_name,
                        label=item.label.strip(),
                    ),
                )
                keep_lookup.add(final_name)

        self._prune_unused_images(images_dir, keep_lookup)
        return keep_images

    def _copy_image(self, images_dir: Path, source_path: Path) -> str:
        target_name = self._unique_name(images_dir, source_path.name)
        shutil.copy2(source_path, images_dir / target_name)
        return target_name

    def _unique_name(self, parent_dir: Path, original_name: str) -> str:
        candidate = Path(original_name).name
        stem = Path(candidate).stem or "image"
        suffix = Path(candidate).suffix
        counter = 1

        while (parent_dir / candidate).exists():
            candidate = f"{stem}_{counter}{suffix}"
            counter += 1
        return candidate

    def _prune_unused_images(self, images_dir: Path, keep_names: set[str]) -> None:
        if not images_dir.exists():
            return

        for child in images_dir.iterdir():
            if child.is_file() and child.name not in keep_names:
                try:
                    child.unlink()
                except OSError:
                    continue


def default_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "data" / "Diary"
    return Path(__file__).resolve().parents[2] / "data" / "Diary"
