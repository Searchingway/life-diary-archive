from __future__ import annotations

import json
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from .book_storage import BookStorage
from .footprint_storage import FootprintStorage
from .lesson_storage import LessonStorage
from .plan_storage import PlanStorage
from .storage import DiaryStorage


MODULE_DIRECTORIES = {
    "diary": ("entries", "日记"),
    "footprint": ("footprints", "足迹"),
    "book": ("books", "读书"),
    "plan": ("plans", "轻计划"),
    "lesson": ("lessons", "教训与反思"),
}

INVALID_FILENAME_CHARS = r'\/:*?"<>|'


def safe_filename(name: str, max_length: int = 60, default_name: str = "未命名") -> str:
    cleaned = re.sub(f"[{re.escape(INVALID_FILENAME_CHARS)}]", "_", str(name or ""))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        cleaned = default_name
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip(" ._")
    return cleaned or default_name


class ExchangePackageExporter:
    def __init__(self, root_dir: Path | str):
        self.root_dir = Path(root_dir)

    def export_module(self, module: str, target_dir: Path | str) -> Path:
        if module not in MODULE_DIRECTORIES:
            raise ValueError(f"未知导出模块：{module}")

        folder_name, title = MODULE_DIRECTORIES[module]
        source_dir = self.root_dir / folder_name
        if not source_dir.exists():
            raise FileNotFoundError(f"暂无可导出的{title}数据。")

        target = Path(target_dir)
        target.mkdir(parents=True, exist_ok=True)

        exported_at = datetime.now().astimezone().isoformat(timespec="seconds")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = self._unique_path(target / f"life_diary_{module}_{timestamp}.zip")

        used_paths: set[str] = set()
        records = self._collect_records(module, exported_at, used_paths)
        if not records:
            raise FileNotFoundError(f"暂无可导出的{title}数据。")

        file_count = 0
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for record in records:
                file_count += self._write_record(archive, record)

            manifest = {
                "app": "life_diary",
                "package_version": 2,
                "module": module,
                "module_title": title,
                "data_directory": folder_name,
                "exported_at": exported_at,
                "file_count": file_count,
                "record_count": len(records),
                "records": [
                    {
                        "module": folder_name,
                        "original_id": record["original_id"],
                        "display_name": record["display_name"],
                        "relative_path": record["relative_path"],
                        "date": record.get("date", ""),
                        "title": record.get("title", ""),
                        "exported_at": exported_at,
                    }
                    for record in records
                ],
            }
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

        return zip_path

    def _collect_records(
        self,
        module: str,
        exported_at: str,
        used_paths: set[str],
    ) -> list[dict[str, Any]]:
        if module == "diary":
            return self._collect_diary_records(exported_at, used_paths)
        if module == "footprint":
            return self._collect_footprint_records(exported_at, used_paths)
        if module == "book":
            return self._collect_book_records(exported_at, used_paths)
        if module == "plan":
            return self._collect_plan_records(exported_at, used_paths)
        if module == "lesson":
            return self._collect_lesson_records(exported_at, used_paths)
        return []

    def _collect_diary_records(self, exported_at: str, used_paths: set[str]) -> list[dict[str, Any]]:
        storage = DiaryStorage(self.root_dir)
        records: list[dict[str, Any]] = []
        for entry in storage.list_entries():
            if not self._has_diary_content(entry, storage.entry_dir(entry.id)):
                continue
            base = f"{entry.date or '未设日期'}_{entry.title.strip() or '日记'}"
            display_name = self._unique_display_name("entries", base, used_paths)
            records.append(
                {
                    "module": "entries",
                    "original_id": entry.id,
                    "display_name": display_name,
                    "relative_path": f"entries/{display_name}",
                    "date": entry.date,
                    "title": entry.title,
                    "source_dir": storage.entry_dir(entry.id),
                    "exported_at": exported_at,
                    "copy_mode": "directory",
                },
            )
        return records

    def _collect_footprint_records(self, exported_at: str, used_paths: set[str]) -> list[dict[str, Any]]:
        storage = FootprintStorage(self.root_dir)
        records: list[dict[str, Any]] = []
        for place in storage.list_places():
            place_dir = storage.footprint_dir(place.id)
            active_visits = [
                visit for visit in place.visits
                if not self._visit_is_deleted(storage.visit_dir(place.id, visit.id))
            ]
            if not self._has_footprint_content(place, place_dir, active_visits):
                continue
            display_name = self._unique_display_name(
                "footprints",
                place.place_name.strip() or "未命名地点",
                used_paths,
            )
            records.append(
                {
                    "module": "footprints",
                    "original_id": place.id,
                    "display_name": display_name,
                    "relative_path": f"footprints/{display_name}",
                    "date": active_visits[0].date if active_visits else "",
                    "title": place.place_name,
                    "source_dir": place_dir,
                    "exported_at": exported_at,
                    "copy_mode": "footprint",
                    "visits": active_visits,
                    "storage": storage,
                },
            )
        return records

    def _collect_book_records(self, exported_at: str, used_paths: set[str]) -> list[dict[str, Any]]:
        storage = BookStorage(self.root_dir)
        records: list[dict[str, Any]] = []
        for book in storage.list_books():
            if not self._has_book_content(book, storage.book_dir(book.id)):
                continue
            base = book.title.strip() or "未命名书籍"
            if self._path_name_used("books", safe_filename(base), used_paths) and book.author.strip():
                base = f"{base}_{book.author.strip()}"
            display_name = self._unique_display_name("books", base, used_paths)
            records.append(
                {
                    "module": "books",
                    "original_id": book.id,
                    "display_name": display_name,
                    "relative_path": f"books/{display_name}",
                    "date": book.finish_date or book.start_date,
                    "title": book.title,
                    "source_dir": storage.book_dir(book.id),
                    "exported_at": exported_at,
                    "copy_mode": "directory",
                },
            )
        return records

    def _collect_plan_records(self, exported_at: str, used_paths: set[str]) -> list[dict[str, Any]]:
        storage = PlanStorage(self.root_dir)
        records: list[dict[str, Any]] = []
        for plan in storage.list_plans():
            if not self._has_plan_content(plan):
                continue
            base = f"{plan.due_date or '未设日期'}_{plan.title.strip() or '轻计划'}"
            display_name = self._unique_display_name("plans", base, used_paths)
            records.append(
                {
                    "module": "plans",
                    "original_id": plan.id,
                    "display_name": display_name,
                    "relative_path": f"plans/{display_name}",
                    "date": plan.due_date,
                    "title": plan.title,
                    "source_dir": storage.plan_dir(plan.id),
                    "exported_at": exported_at,
                    "copy_mode": "directory",
                },
            )
        return records

    def _collect_lesson_records(self, exported_at: str, used_paths: set[str]) -> list[dict[str, Any]]:
        storage = LessonStorage(self.root_dir)
        records: list[dict[str, Any]] = []
        for lesson in storage.list_lessons():
            if not self._has_lesson_content(lesson, storage.lesson_dir(lesson.id)):
                continue
            base = f"{lesson.date or '未设日期'}_{lesson.title.strip() or '教训'}"
            display_name = self._unique_display_name("lessons", base, used_paths)
            records.append(
                {
                    "module": "lessons",
                    "original_id": lesson.id,
                    "display_name": display_name,
                    "relative_path": f"lessons/{display_name}",
                    "date": lesson.date,
                    "title": lesson.title,
                    "source_dir": storage.lesson_dir(lesson.id),
                    "exported_at": exported_at,
                    "copy_mode": "directory",
                },
            )
        return records

    def _write_record(self, archive: zipfile.ZipFile, record: dict[str, Any]) -> int:
        if record["copy_mode"] == "footprint":
            return self._write_footprint_record(archive, record)
        return self._write_directory(archive, record["source_dir"], record["relative_path"])

    def _write_directory(self, archive: zipfile.ZipFile, source_dir: Path, relative_path: str) -> int:
        count = 0
        for file_path in source_dir.rglob("*"):
            if not file_path.is_file():
                continue
            arcname = f"{relative_path}/{file_path.relative_to(source_dir).as_posix()}"
            archive.write(file_path, arcname)
            count += 1
        return count

    def _write_footprint_record(self, archive: zipfile.ZipFile, record: dict[str, Any]) -> int:
        source_dir: Path = record["source_dir"]
        relative_path = record["relative_path"]
        storage: FootprintStorage = record["storage"]
        visits = record["visits"]
        count = 0

        metadata_path = source_dir / "footprint.json"
        if metadata_path.exists():
            with metadata_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            data["visit_ids"] = [visit.id for visit in visits]
            archive.writestr(
                f"{relative_path}/footprint.json",
                json.dumps(data, ensure_ascii=False, indent=2),
            )
            count += 1

        for file_name in ("summary.md",):
            file_path = source_dir / file_name
            if file_path.exists() and file_path.is_file():
                archive.write(file_path, f"{relative_path}/{file_name}")
                count += 1

        place_image_dir = source_dir / "images"
        if place_image_dir.exists():
            count += self._write_directory(archive, place_image_dir, f"{relative_path}/images")

        used_visit_paths: set[str] = set()
        for visit in visits:
            visit_dir = storage.visit_dir(record["original_id"], visit.id)
            if not visit_dir.exists():
                continue
            visit_name = self._unique_child_name(
                visit.date.strip() or "未设日期",
                used_visit_paths,
            )
            count += self._write_directory(
                archive,
                visit_dir,
                f"{relative_path}/visits/{visit_name}",
            )
        return count

    def _has_diary_content(self, entry: Any, entry_dir: Path) -> bool:
        return bool(
            entry.title.strip()
            or entry.body.strip()
            or entry.images
            or self._directory_has_files(entry_dir / "images")
        )

    def _has_footprint_content(self, place: Any, place_dir: Path, active_visits: list[Any]) -> bool:
        return bool(
            place.place_name.strip()
            or place.summary.strip()
            or place.images
            or active_visits
            or self._directory_has_files(place_dir / "images")
        )

    def _has_book_content(self, book: Any, book_dir: Path) -> bool:
        return bool(
            book.title.strip()
            or book.author.strip()
            or book.tags
            or book.summary.strip()
            or book.notes.strip()
            or book.images
            or book.related_diaries
            or self._directory_has_files(book_dir / "images")
        )

    def _has_plan_content(self, plan: Any) -> bool:
        return bool(
            plan.title.strip()
            or plan.notes.strip()
            or plan.tags
            or plan.trigger_scene.strip()
            or plan.avoid_behavior.strip()
            or plan.reason.strip()
            or plan.alternative_action.strip()
        )

    def _has_lesson_content(self, lesson: Any, lesson_dir: Path) -> bool:
        return bool(
            lesson.title.strip()
            or lesson.tags
            or lesson.event.strip()
            or lesson.judgment.strip()
            or lesson.result.strip()
            or lesson.mistake.strip()
            or lesson.root_cause.strip()
            or lesson.cost.strip()
            or lesson.next_action.strip()
            or lesson.one_sentence.strip()
            or lesson.images
            or lesson.related_diaries
            or self._directory_has_files(lesson_dir / "images")
        )

    def _visit_is_deleted(self, visit_dir: Path) -> bool:
        metadata_path = visit_dir / "visit.json"
        if not metadata_path.exists():
            return False
        try:
            with metadata_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (json.JSONDecodeError, OSError):
            return True
        return bool(data.get("deleted"))

    def _directory_has_files(self, directory: Path) -> bool:
        return directory.exists() and any(path.is_file() for path in directory.rglob("*"))

    def _unique_display_name(self, module_dir: str, name: str, used_paths: set[str]) -> str:
        base = safe_filename(name)
        candidate = base
        counter = 2
        while self._path_name_used(module_dir, candidate, used_paths):
            candidate = safe_filename(f"{base}_{counter:02d}")
            counter += 1
        used_paths.add(f"{module_dir}/{candidate}")
        return candidate

    def _unique_child_name(self, name: str, used_names: set[str]) -> str:
        base = safe_filename(name)
        candidate = base
        counter = 2
        while candidate in used_names:
            candidate = safe_filename(f"{base}_{counter:02d}")
            counter += 1
        used_names.add(candidate)
        return candidate

    def _path_name_used(self, module_dir: str, name: str, used_paths: set[str]) -> bool:
        return f"{module_dir}/{name}" in used_paths

    def _unique_path(self, path: Path) -> Path:
        if not path.exists():
            return path

        counter = 1
        while True:
            candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
            if not candidate.exists():
                return candidate
            counter += 1
