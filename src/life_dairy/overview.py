from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from .book_storage import BookStorage
from .footprint_storage import FootprintStorage
from .lesson_storage import LessonStorage
from .plan_storage import PlanStorage
from .storage import DiaryStorage


@dataclass(slots=True)
class OverviewStats:
    month_diary_count: int = 0
    month_diary_chars: int = 0
    month_diary_images: int = 0
    month_completed_plans: int = 0
    year_diary_count: int = 0
    year_diary_chars: int = 0
    year_diary_images: int = 0
    year_completed_plans: int = 0


@dataclass(slots=True)
class TimelineItem:
    record_type: str
    record_id: str
    date: str
    title: str
    summary: str
    image_count: int = 0
    status: str = ""
    source_module: str = ""
    sort_key: str = ""


class OverviewService:
    def __init__(
        self,
        diary_storage: DiaryStorage,
        footprint_storage: FootprintStorage,
        book_storage: BookStorage,
        plan_storage: PlanStorage,
        lesson_storage: LessonStorage,
    ):
        self.diary_storage = diary_storage
        self.footprint_storage = footprint_storage
        self.book_storage = book_storage
        self.plan_storage = plan_storage
        self.lesson_storage = lesson_storage

    def build_stats(self, today: date | None = None) -> OverviewStats:
        current = today or date.today()
        month_prefix = current.strftime("%Y-%m")
        year_prefix = current.strftime("%Y")
        stats = OverviewStats()

        for entry in self.diary_storage.list_entries():
            entry_date = entry.date or ""
            char_count = len(entry.body or "")
            image_count = self._count_files(self.diary_storage.image_dir(entry.id))
            if entry_date.startswith(month_prefix):
                stats.month_diary_count += 1
                stats.month_diary_chars += char_count
                stats.month_diary_images += image_count
            if entry_date.startswith(year_prefix):
                stats.year_diary_count += 1
                stats.year_diary_chars += char_count
                stats.year_diary_images += image_count

        for plan in self.plan_storage.list_plans():
            if not self._is_completed_status(plan.status):
                continue
            plan_date = plan.due_date or self._date_from_iso(plan.updated_at)
            if plan_date.startswith(month_prefix):
                stats.month_completed_plans += 1
            if plan_date.startswith(year_prefix):
                stats.year_completed_plans += 1

        return stats

    def build_timeline(self, limit: int = 30) -> list[TimelineItem]:
        items: list[TimelineItem] = []
        items.extend(self._diary_items())
        items.extend(self._footprint_items())
        items.extend(self._book_items())
        items.extend(self._plan_items())
        items.extend(self._lesson_items())
        items.sort(key=lambda item: (item.date or "", item.sort_key, item.title), reverse=True)
        return items[:limit]

    def _diary_items(self) -> list[TimelineItem]:
        items = []
        for entry in self.diary_storage.list_entries():
            items.append(
                TimelineItem(
                    record_type="日记",
                    record_id=entry.id,
                    date=entry.date,
                    title=entry.display_title,
                    summary=self._summary(entry.body),
                    image_count=self._count_files(self.diary_storage.image_dir(entry.id)),
                    source_module="entries",
                    sort_key=entry.updated_at,
                ),
            )
        return items

    def _footprint_items(self) -> list[TimelineItem]:
        items = []
        for place in self.footprint_storage.list_places():
            for visit in place.visits:
                items.append(
                    TimelineItem(
                        record_type="足迹",
                        record_id=f"{place.id}:{visit.id}",
                        date=visit.date,
                        title=place.display_title,
                        summary=self._summary(visit.thought or place.summary),
                        image_count=self._count_files(self.footprint_storage.visit_image_dir(place.id, visit.id)),
                        source_module="footprints",
                        sort_key=visit.updated_at,
                    ),
                )
        return items

    def _book_items(self) -> list[TimelineItem]:
        items = []
        for book in self.book_storage.list_books():
            item_date = book.finish_date or book.start_date or self._date_from_iso(book.updated_at)
            items.append(
                TimelineItem(
                    record_type="读书",
                    record_id=book.id,
                    date=item_date,
                    title=book.display_title,
                    summary=self._summary(book.notes or book.summary),
                    image_count=self._count_files(self.book_storage.image_dir(book.id)),
                    status=book.status,
                    source_module="books",
                    sort_key=book.updated_at,
                ),
            )
        return items

    def _plan_items(self) -> list[TimelineItem]:
        items = []
        for plan in self.plan_storage.list_plans():
            plan_type = "减法" if plan.plan_type == "subtract" else "加法"
            status = plan.status or ("已完成" if self._is_completed_status(plan.status) else "未完成")
            summary = plan.notes
            if plan.plan_type == "subtract":
                summary = plan.alternative_action or plan.avoid_behavior or plan.trigger_scene or plan.notes
            items.append(
                TimelineItem(
                    record_type="计划",
                    record_id=plan.id,
                    date=plan.due_date or self._date_from_iso(plan.updated_at),
                    title=f"【{plan_type}】{plan.display_title}",
                    summary=self._summary(summary),
                    status=status,
                    source_module="plans",
                    sort_key=plan.updated_at,
                ),
            )
        return items

    def _lesson_items(self) -> list[TimelineItem]:
        items = []
        for lesson in self.lesson_storage.list_lessons():
            summary = (
                lesson.event
                or lesson.mistake
                or lesson.next_action
                or lesson.one_sentence
            )
            items.append(
                TimelineItem(
                    record_type="教训",
                    record_id=lesson.id,
                    date=lesson.date,
                    title=lesson.display_title,
                    summary=self._summary(summary),
                    image_count=self._count_files(self.lesson_storage.image_dir(lesson.id)),
                    status=lesson.severity,
                    source_module="lessons",
                    sort_key=lesson.updated_at,
                ),
            )
        return items

    def _count_files(self, directory: Path) -> int:
        if not directory.exists():
            return 0
        try:
            return sum(1 for child in directory.iterdir() if child.is_file())
        except OSError:
            return 0

    def _summary(self, text: str, limit: int = 80) -> str:
        compact = " ".join((text or "").split())
        return compact[:limit]

    def _date_from_iso(self, value: str) -> str:
        if not value:
            return ""
        try:
            return datetime.fromisoformat(value).date().isoformat()
        except ValueError:
            return value[:10]

    def _is_completed_status(self, status: str) -> bool:
        normalized = (status or "").strip()
        return normalized in {"已完成", "已做到"} or "完成" in normalized or "做到" in normalized
