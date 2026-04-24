from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from .models import BookEntry, BookImage, BookImageDraft, now_iso


class BookStorage:
    def __init__(self, root_dir: Path | str):
        self.root_dir = Path(root_dir)
        self.books_dir = self.root_dir / "books"
        self.books_dir.mkdir(parents=True, exist_ok=True)

    def create_empty_book(self) -> BookEntry:
        timestamp = now_iso()
        return BookEntry(
            id=uuid4().hex,
            title="",
            author="",
            status="想读",
            start_date="",
            finish_date="",
            tags=[],
            summary="",
            notes="",
            created_at=timestamp,
            updated_at=timestamp,
            images=[],
            related_diaries=[],
        )

    def book_dir(self, book_id: str) -> Path:
        return self.books_dir / book_id

    def image_dir(self, book_id: str) -> Path:
        return self.book_dir(book_id) / "images"

    def resolve_image_path(self, book_id: str, image_name: str) -> Path:
        return self.image_dir(book_id) / image_name

    def list_books(self, query: str = "") -> list[BookEntry]:
        keyword = query.strip().lower()
        items: list[BookEntry] = []
        for child in self.books_dir.iterdir():
            if not child.is_dir():
                continue
            try:
                book = self._load_book_from_directory(child, include_deleted=False)
            except (FileNotFoundError, KeyError, json.JSONDecodeError, OSError, ValueError):
                continue
            if keyword and not self._matches_query(book, keyword):
                continue
            items.append(book)

        items.sort(key=lambda item: (item.updated_at, item.created_at, item.display_title.lower()), reverse=True)
        return items

    def save_book(
        self,
        book: BookEntry,
        image_items: Iterable[BookImageDraft] | None = None,
    ) -> BookEntry:
        book_dir = self.book_dir(book.id)
        book_dir.mkdir(parents=True, exist_ok=True)

        book.updated_at = now_iso()

        if image_items is not None:
            book.images = self._sync_images(book.id, image_items)

        metadata_path = book_dir / "book.json"
        summary_path = book_dir / "summary.md"
        notes_path = book_dir / "notes.md"

        with metadata_path.open("w", encoding="utf-8") as file:
            json.dump(book.to_dict(), file, ensure_ascii=False, indent=2)

        summary_path.write_text(book.summary, encoding="utf-8")
        notes_path.write_text(book.notes, encoding="utf-8")
        return self.load_book(book.id)

    def load_book(self, book_id: str) -> BookEntry:
        return self._load_book_from_directory(self.book_dir(book_id), include_deleted=True)

    def delete_book(self, book_id: str) -> None:
        book_dir = self.book_dir(book_id)
        if not book_dir.exists():
            raise FileNotFoundError(f"找不到要删除的读书笔记：{book_id}")
        metadata_path = book_dir / "book.json"
        with metadata_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        data["deleted"] = True
        data["deleted_at"] = now_iso()
        data["updated_at"] = now_iso()
        with metadata_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def _load_book_from_directory(self, book_dir: Path, include_deleted: bool) -> BookEntry:
        metadata_path = book_dir / "book.json"
        summary_path = book_dir / "summary.md"
        notes_path = book_dir / "notes.md"

        with metadata_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if data.get("deleted") and not include_deleted:
            raise ValueError("book deleted")

        summary = summary_path.read_text(encoding="utf-8") if summary_path.exists() else ""
        notes = notes_path.read_text(encoding="utf-8") if notes_path.exists() else ""
        return BookEntry.from_dict(data, summary, notes)

    def _matches_query(self, book: BookEntry, keyword: str) -> bool:
        haystacks = [
            book.title,
            book.author,
            book.status,
            " ".join(book.tags),
            book.summary,
            book.notes,
            " ".join(image.label for image in book.images if image.label),
            " ".join(item.display_title for item in book.related_diaries),
        ]
        return any(keyword in text.lower() for text in haystacks if text)

    def _sync_images(
        self,
        book_id: str,
        image_items: Iterable[BookImageDraft],
    ) -> list[BookImage]:
        images_dir = self.image_dir(book_id)
        images_dir.mkdir(parents=True, exist_ok=True)

        keep_images: list[BookImage] = []
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
                    BookImage(
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
