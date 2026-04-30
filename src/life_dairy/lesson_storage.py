from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from .models import LessonEntry, LessonImage, LessonImageDraft, now_iso


LESSON_CATEGORIES = ["学习", "接单", "情绪", "人际", "金钱", "项目", "身体", "其他"]
LESSON_SEVERITIES = ["轻微", "中等", "重要", "严重"]
LESSON_SECTIONS = [
    "事件经过",
    "当时我是怎么判断的",
    "结果是什么",
    "我哪里判断错了",
    "真正的问题是什么",
    "这次的代价",
    "下次遇到类似情况要怎么做",
    "一句话教训",
]


class LessonStorage:
    def __init__(self, root_dir: Path | str):
        self.root_dir = Path(root_dir)
        self.lessons_dir = self.root_dir / "lessons"
        self.lessons_dir.mkdir(parents=True, exist_ok=True)

    def create_empty_lesson(self) -> LessonEntry:
        timestamp = now_iso()
        return LessonEntry(
            id=uuid4().hex,
            title="",
            date=date.today().isoformat(),
            category="其他",
            severity="中等",
            tags=[],
            event="",
            judgment="",
            result="",
            mistake="",
            root_cause="",
            cost="",
            next_action="",
            one_sentence="",
            created_at=timestamp,
            updated_at=timestamp,
            images=[],
            related_diaries=[],
        )

    def lesson_dir(self, lesson_id: str) -> Path:
        return self.lessons_dir / lesson_id

    def image_dir(self, lesson_id: str) -> Path:
        return self.lesson_dir(lesson_id) / "images"

    def resolve_image_path(self, lesson_id: str, image_name: str) -> Path:
        return self.image_dir(lesson_id) / image_name

    def list_lessons(self, query: str = "", category: str = "全部") -> list[LessonEntry]:
        keyword = query.strip().lower()
        selected_category = category.strip()
        items: list[LessonEntry] = []
        for child in self.lessons_dir.iterdir():
            if not child.is_dir():
                continue
            try:
                lesson = self._load_lesson_from_directory(child, include_deleted=False)
            except (FileNotFoundError, KeyError, json.JSONDecodeError, OSError, ValueError):
                continue
            if selected_category and selected_category != "全部" and lesson.category != selected_category:
                continue
            if keyword and not self._matches_query(lesson, keyword):
                continue
            items.append(lesson)

        items.sort(key=lambda item: (item.date, item.updated_at, item.created_at), reverse=True)
        return items

    def save_lesson(
        self,
        lesson: LessonEntry,
        image_items: Iterable[LessonImageDraft] | None = None,
    ) -> LessonEntry:
        lesson_dir = self.lesson_dir(lesson.id)
        lesson_dir.mkdir(parents=True, exist_ok=True)

        lesson.updated_at = now_iso()
        if lesson.category not in LESSON_CATEGORIES:
            lesson.category = "其他"
        if lesson.severity not in LESSON_SEVERITIES:
            lesson.severity = "中等"

        if image_items is not None:
            lesson.images = self._sync_images(lesson.id, image_items)

        with (lesson_dir / "lesson.json").open("w", encoding="utf-8") as file:
            json.dump(lesson.to_dict(), file, ensure_ascii=False, indent=2)
        (lesson_dir / "content.md").write_text(self._build_content(lesson), encoding="utf-8")
        return self.load_lesson(lesson.id)

    def load_lesson(self, lesson_id: str) -> LessonEntry:
        return self._load_lesson_from_directory(self.lesson_dir(lesson_id), include_deleted=True)

    def delete_lesson(self, lesson_id: str) -> None:
        lesson_dir = self.lesson_dir(lesson_id)
        if not lesson_dir.exists():
            raise FileNotFoundError(f"找不到要删除的反思记录：{lesson_id}")
        metadata_path = lesson_dir / "lesson.json"
        with metadata_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        data["deleted"] = True
        data["deleted_at"] = now_iso()
        data["updated_at"] = now_iso()
        with metadata_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def _load_lesson_from_directory(self, lesson_dir: Path, include_deleted: bool) -> LessonEntry:
        with (lesson_dir / "lesson.json").open("r", encoding="utf-8") as file:
            data = json.load(file)

        if data.get("deleted") and not include_deleted:
            raise ValueError("lesson deleted")

        content_path = lesson_dir / "content.md"
        content = content_path.read_text(encoding="utf-8") if content_path.exists() else ""
        return LessonEntry.from_dict(data, self._parse_content(content))

    def _matches_query(self, lesson: LessonEntry, keyword: str) -> bool:
        haystacks = [
            lesson.title,
            lesson.date,
            lesson.category,
            lesson.severity,
            " ".join(lesson.tags),
            lesson.event,
            lesson.judgment,
            lesson.result,
            lesson.mistake,
            lesson.root_cause,
            lesson.cost,
            lesson.next_action,
            lesson.one_sentence,
            " ".join(image.label for image in lesson.images if image.label),
            " ".join(item.display_title for item in lesson.related_diaries),
        ]
        return any(keyword in text.lower() for text in haystacks if text)

    def _build_content(self, lesson: LessonEntry) -> str:
        values = {
            "事件经过": lesson.event,
            "当时我是怎么判断的": lesson.judgment,
            "结果是什么": lesson.result,
            "我哪里判断错了": lesson.mistake,
            "真正的问题是什么": lesson.root_cause,
            "这次的代价": lesson.cost,
            "下次遇到类似情况要怎么做": lesson.next_action,
            "一句话教训": lesson.one_sentence,
        }
        parts = []
        for title in LESSON_SECTIONS:
            parts.append(f"## {title}\n\n{values.get(title, '').rstrip()}\n")
        return "\n".join(parts).rstrip() + "\n"

    def _parse_content(self, content: str) -> dict[str, str]:
        sections = {title: "" for title in LESSON_SECTIONS}
        current_title: str | None = None
        current_lines: list[str] = []

        def flush() -> None:
            if current_title in sections:
                sections[current_title] = "\n".join(current_lines).strip()

        for line in content.splitlines():
            if line.startswith("## "):
                flush()
                title = line[3:].strip()
                current_title = title if title in sections else None
                current_lines = []
                continue
            if current_title is not None:
                current_lines.append(line)
        flush()
        return sections

    def _sync_images(
        self,
        lesson_id: str,
        image_items: Iterable[LessonImageDraft],
    ) -> list[LessonImage]:
        images_dir = self.image_dir(lesson_id)
        images_dir.mkdir(parents=True, exist_ok=True)

        keep_images: list[LessonImage] = []
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
                keep_images.append(LessonImage(file_name=final_name, label=item.label.strip()))
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
