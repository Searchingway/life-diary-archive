from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from .book_storage import BookStorage
from .models import WorkEntry, WorkImage, WorkImageDraft, now_iso


WORK_TYPES = ["书籍", "电影", "纪录片", "动漫", "动画", "游戏", "文章", "音乐", "课程", "视频", "展览", "其他"]
WORK_STATUSES = ["想看", "进行中", "已完成", "暂停", "放弃"]
WORK_SECTIONS = [
    "一句话印象",
    "内容摘要",
    "我喜欢的地方",
    "我不喜欢的地方",
    "触动我的地方",
    "喜欢的角色 / 场景 / 台词",
    "让我想到的自己",
    "和我过去经历的关联",
    "我的最终评价",
]


class WorkStorage:
    def __init__(self, root_dir: Path | str):
        self.root_dir = Path(root_dir)
        self.works_dir = self.root_dir / "works"
        self.book_storage = BookStorage(self.root_dir)
        self.works_dir.mkdir(parents=True, exist_ok=True)

    def create_empty_work(self) -> WorkEntry:
        timestamp = now_iso()
        return WorkEntry(
            id=uuid4().hex,
            title="",
            work_type="其他",
            creator="",
            status="想看",
            start_date="",
            finish_date="",
            rating="",
            tags=[],
            one_sentence="",
            summary="",
            liked="",
            disliked="",
            touched="",
            favorite_parts="",
            self_connection="",
            past_connection="",
            final_review="",
            created_at=timestamp,
            updated_at=timestamp,
            images=[],
            related_diaries=[],
            related_self_analysis=[],
        )

    def work_dir(self, work_id: str) -> Path:
        return self.works_dir / work_id

    def image_dir(self, work_id: str) -> Path:
        if not self.work_dir(work_id).exists() and self.book_storage.book_dir(work_id).exists():
            return self.book_storage.image_dir(work_id)
        return self.work_dir(work_id) / "images"

    def resolve_image_path(self, work_id: str, image_name: str) -> Path:
        return self.image_dir(work_id) / image_name

    def record_exists(self, work_id: str) -> bool:
        return self.work_dir(work_id).exists() or self.book_storage.book_dir(work_id).exists()

    def list_works(self, query: str = "", work_type: str = "全部") -> list[WorkEntry]:
        keyword = query.strip().lower()
        selected_type = work_type.strip()
        items: list[WorkEntry] = []

        for child in self.works_dir.iterdir():
            if not child.is_dir():
                continue
            try:
                work = self._load_work_from_directory(child, include_deleted=False)
            except (FileNotFoundError, KeyError, json.JSONDecodeError, OSError, ValueError):
                continue
            if selected_type and selected_type != "全部" and work.work_type != selected_type:
                continue
            if keyword and not self._matches_query(work, keyword):
                continue
            items.append(work)

        existing_ids = {item.id for item in items}
        for book in self.book_storage.list_books(query):
            if book.id in existing_ids:
                continue
            work = self._book_to_work(book)
            if selected_type and selected_type != "全部" and work.work_type != selected_type:
                continue
            if keyword and not self._matches_query(work, keyword):
                continue
            items.append(work)

        items.sort(
            key=lambda item: (
                item.finish_date or item.start_date,
                item.updated_at,
                item.created_at,
            ),
            reverse=True,
        )
        return items

    def save_work(
        self,
        work: WorkEntry,
        image_items: Iterable[WorkImageDraft] | None = None,
    ) -> WorkEntry:
        work_dir = self.work_dir(work.id)
        work_dir.mkdir(parents=True, exist_ok=True)

        work.updated_at = now_iso()
        if work.work_type not in WORK_TYPES:
            work.work_type = "其他"
        if work.status not in WORK_STATUSES:
            work.status = "想看"

        if image_items is not None:
            work.images = self._sync_images(work.id, image_items)

        with (work_dir / "work.json").open("w", encoding="utf-8") as file:
            json.dump(work.to_dict(), file, ensure_ascii=False, indent=2)
        (work_dir / "content.md").write_text(self._build_content(work), encoding="utf-8")
        return self.load_work(work.id)

    def load_work(self, work_id: str) -> WorkEntry:
        if self.work_dir(work_id).exists():
            return self._load_work_from_directory(self.work_dir(work_id), include_deleted=True)
        if self.book_storage.book_dir(work_id).exists():
            return self._book_to_work(self.book_storage.load_book(work_id))
        return self._load_work_from_directory(self.work_dir(work_id), include_deleted=True)

    def delete_work(self, work_id: str) -> None:
        work_dir = self.work_dir(work_id)
        if not work_dir.exists() and self.book_storage.book_dir(work_id).exists():
            self.book_storage.delete_book(work_id)
            return
        if not work_dir.exists():
            raise FileNotFoundError(f"找不到要删除的作品感悟记录：{work_id}")
        metadata_path = work_dir / "work.json"
        with metadata_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        data["deleted"] = True
        data["deleted_at"] = now_iso()
        data["updated_at"] = now_iso()
        with metadata_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def _load_work_from_directory(self, work_dir: Path, include_deleted: bool) -> WorkEntry:
        with (work_dir / "work.json").open("r", encoding="utf-8") as file:
            data = json.load(file)

        if data.get("deleted") and not include_deleted:
            raise ValueError("work deleted")

        content_path = work_dir / "content.md"
        content = content_path.read_text(encoding="utf-8") if content_path.exists() else ""
        return WorkEntry.from_dict(data, self._parse_content(content))

    def _matches_query(self, work: WorkEntry, keyword: str) -> bool:
        haystacks = [
            work.title,
            work.work_type,
            work.creator,
            work.status,
            work.start_date,
            work.finish_date,
            work.rating,
            " ".join(work.tags),
            work.one_sentence,
            work.summary,
            work.liked,
            work.disliked,
            work.touched,
            work.favorite_parts,
            work.self_connection,
            work.past_connection,
            work.final_review,
            " ".join(image.label for image in work.images if image.label),
            " ".join(item.display_title for item in work.related_diaries),
            " ".join(item.display_title for item in work.related_self_analysis),
        ]
        return any(keyword in text.lower() for text in haystacks if text)

    def _book_to_work(self, book) -> WorkEntry:
        return WorkEntry(
            id=book.id,
            title=book.title,
            work_type="书籍",
            creator=book.author,
            status=book.status,
            start_date=book.start_date,
            finish_date=book.finish_date,
            rating="",
            tags=book.tags,
            one_sentence=book.summary,
            summary=book.summary,
            liked="",
            disliked="",
            touched=book.notes,
            favorite_parts="",
            self_connection="",
            past_connection="",
            final_review=book.notes,
            created_at=book.created_at,
            updated_at=book.updated_at,
            images=[WorkImage(file_name=image.file_name, label=image.label) for image in book.images],
            related_diaries=[],
            related_self_analysis=[],
        )

    def _build_content(self, work: WorkEntry) -> str:
        values = {
            "一句话印象": work.one_sentence,
            "内容摘要": work.summary,
            "我喜欢的地方": work.liked,
            "我不喜欢的地方": work.disliked,
            "触动我的地方": work.touched,
            "喜欢的角色 / 场景 / 台词": work.favorite_parts,
            "让我想到的自己": work.self_connection,
            "和我过去经历的关联": work.past_connection,
            "我的最终评价": work.final_review,
        }
        parts = []
        for title in WORK_SECTIONS:
            parts.append(f"# {title}\n\n{values.get(title, '').rstrip()}\n")
        return "\n".join(parts).rstrip() + "\n"

    def _parse_content(self, content: str) -> dict[str, str]:
        sections = {title: "" for title in WORK_SECTIONS}
        current_title: str | None = None
        current_lines: list[str] = []

        def flush() -> None:
            if current_title in sections:
                sections[current_title] = "\n".join(current_lines).strip()

        for line in content.splitlines():
            if line.startswith("# "):
                flush()
                title = line[2:].strip()
                current_title = title if title in sections else None
                current_lines = []
                continue
            if current_title is not None:
                current_lines.append(line)
        flush()
        return sections

    def _sync_images(
        self,
        work_id: str,
        image_items: Iterable[WorkImageDraft],
    ) -> list[WorkImage]:
        images_dir = self.image_dir(work_id)
        images_dir.mkdir(parents=True, exist_ok=True)

        keep_images: list[WorkImage] = []
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
                keep_images.append(WorkImage(file_name=final_name, label=item.label.strip()))
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
