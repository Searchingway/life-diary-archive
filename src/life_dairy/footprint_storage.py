from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from .models import (
    FootprintImage,
    FootprintImageDraft,
    FootprintPlace,
    FootprintVisit,
    now_iso,
)


class FootprintStorage:
    def __init__(self, root_dir: Path | str):
        self.root_dir = Path(root_dir)
        self.footprints_dir = self.root_dir / "footprints"
        self.footprints_dir.mkdir(parents=True, exist_ok=True)

    def create_empty_place(self) -> FootprintPlace:
        timestamp = now_iso()
        return FootprintPlace(
            id=uuid4().hex,
            place_name="",
            summary="",
            created_at=timestamp,
            updated_at=timestamp,
            images=[],
            visits=[],
        )

    def create_empty_visit(self, target_date: str | None = None) -> FootprintVisit:
        timestamp = now_iso()
        return FootprintVisit(
            id=uuid4().hex,
            date=target_date or date.today().isoformat(),
            thought="",
            created_at=timestamp,
            updated_at=timestamp,
            related_entry_id="",
            images=[],
        )

    # Backward-compatible aliases kept to reduce ripple in older code paths.
    def create_empty_footprint(self) -> FootprintPlace:
        return self.create_empty_place()

    def footprint_dir(self, place_id: str) -> Path:
        return self.footprints_dir / place_id

    def place_image_dir(self, place_id: str) -> Path:
        return self.footprint_dir(place_id) / "images"

    def visits_dir(self, place_id: str) -> Path:
        return self.footprint_dir(place_id) / "visits"

    def visit_dir(self, place_id: str, visit_id: str) -> Path:
        return self.visits_dir(place_id) / visit_id

    def visit_image_dir(self, place_id: str, visit_id: str) -> Path:
        return self.visit_dir(place_id, visit_id) / "images"

    def resolve_place_image_path(self, place_id: str, image_name: str) -> Path:
        return self.place_image_dir(place_id) / image_name

    def resolve_visit_image_path(self, place_id: str, visit_id: str, image_name: str) -> Path:
        candidate = self.visit_image_dir(place_id, visit_id) / image_name
        if candidate.exists():
            return candidate
        if visit_id.endswith("_legacy"):
            legacy_path = self.place_image_dir(place_id) / image_name
            if legacy_path.exists():
                return legacy_path
        return candidate

    def list_places(self, query: str = "") -> list[FootprintPlace]:
        keyword = query.strip().lower()
        items: list[FootprintPlace] = []
        for child in self.footprints_dir.iterdir():
            if not child.is_dir():
                continue
            try:
                place = self._load_place_from_directory(child, include_deleted=False)
            except (FileNotFoundError, KeyError, json.JSONDecodeError, OSError, ValueError):
                continue
            if keyword and not self._matches_query(place, keyword):
                continue
            items.append(place)

        items.sort(key=lambda item: (item.updated_at, item.created_at, item.display_title.lower()), reverse=True)
        return items

    def list_place_visits_by_date(self, target_date: str) -> list[tuple[FootprintPlace, FootprintVisit]]:
        items: list[tuple[FootprintPlace, FootprintVisit]] = []
        for place in self.list_places():
            for visit in place.visits:
                if visit.date == target_date:
                    items.append((place, visit))

        items.sort(
            key=lambda item: (
                item[1].date,
                item[1].created_at,
                item[1].updated_at,
                item[0].display_title.lower(),
            ),
        )
        return items

    def list_footprints_by_date(self, target_date: str) -> list[tuple[FootprintPlace, FootprintVisit]]:
        return self.list_place_visits_by_date(target_date)

    def save_place(
        self,
        place: FootprintPlace,
        place_image_items: Iterable[FootprintImageDraft] | None = None,
        visit_image_items: dict[str, Iterable[FootprintImageDraft]] | None = None,
    ) -> FootprintPlace:
        place_dir = self.footprint_dir(place.id)
        place_dir.mkdir(parents=True, exist_ok=True)

        place.updated_at = now_iso()

        if place_image_items is not None:
            place.images = self._sync_images(self.place_image_dir(place.id), place_image_items)

        metadata_path = place_dir / "footprint.json"
        summary_path = place_dir / "summary.md"

        summary_path.write_text(place.summary, encoding="utf-8")
        self._save_visits(place, visit_image_items or {})

        with metadata_path.open("w", encoding="utf-8") as file:
            json.dump(place.to_dict(), file, ensure_ascii=False, indent=2)

        self._prune_removed_visits(place.id, {visit.id for visit in place.visits})
        return self.load_place(place.id)

    def save_footprint(
        self,
        place: FootprintPlace,
        place_image_items: Iterable[FootprintImageDraft] | None = None,
        visit_image_items: dict[str, Iterable[FootprintImageDraft]] | None = None,
    ) -> FootprintPlace:
        return self.save_place(place, place_image_items, visit_image_items)

    def load_place(self, place_id: str) -> FootprintPlace:
        return self._load_place_from_directory(
            self.footprint_dir(place_id),
            include_deleted=True,
        )

    def load_footprint(self, place_id: str) -> FootprintPlace:
        return self.load_place(place_id)

    def delete_place(self, place_id: str) -> None:
        place_dir = self.footprint_dir(place_id)
        if not place_dir.exists():
            raise FileNotFoundError(f"找不到要删除的地点足迹：{place_id}")
        metadata_path = place_dir / "footprint.json"
        with metadata_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        data["deleted"] = True
        data["deleted_at"] = now_iso()
        data["updated_at"] = now_iso()
        with metadata_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def delete_footprint(self, place_id: str) -> None:
        self.delete_place(place_id)

    def _save_visits(
        self,
        place: FootprintPlace,
        visit_image_items: dict[str, Iterable[FootprintImageDraft]],
    ) -> None:
        self.visits_dir(place.id).mkdir(parents=True, exist_ok=True)

        for visit in place.visits:
            visit_dir = self.visit_dir(place.id, visit.id)
            visit_dir.mkdir(parents=True, exist_ok=True)
            visit.updated_at = now_iso()

            if visit.id in visit_image_items:
                visit.images = self._sync_images(
                    self.visit_image_dir(place.id, visit.id),
                    visit_image_items[visit.id],
                )

            with (visit_dir / "visit.json").open("w", encoding="utf-8") as file:
                json.dump(visit.to_dict(), file, ensure_ascii=False, indent=2)
            (visit_dir / "thought.md").write_text(visit.thought, encoding="utf-8")

    def _prune_removed_visits(self, place_id: str, keep_ids: set[str]) -> None:
        visits_dir = self.visits_dir(place_id)
        if not visits_dir.exists():
            return

        for child in visits_dir.iterdir():
            if child.is_dir() and child.name not in keep_ids:
                shutil.rmtree(child, ignore_errors=True)

    def _load_place_from_directory(
        self,
        place_dir: Path,
        include_deleted: bool,
    ) -> FootprintPlace:
        metadata_path = place_dir / "footprint.json"
        with metadata_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if data.get("deleted") and not include_deleted:
            raise ValueError("footprint deleted")

        if "visit_ids" not in data and "summary_file" not in data:
            return self._load_legacy_place(place_dir, data)

        summary = ""
        summary_path = place_dir / str(data.get("summary_file", "summary.md"))
        if summary_path.exists():
            summary = summary_path.read_text(encoding="utf-8")

        visits: list[FootprintVisit] = []
        visit_ids = [str(item) for item in data.get("visit_ids", [])]
        for visit_id in visit_ids:
            try:
                visits.append(self._load_visit(place_dir, visit_id))
            except (FileNotFoundError, KeyError, json.JSONDecodeError, OSError, ValueError):
                continue

        return FootprintPlace.from_dict(data, summary, visits)

    def _load_visit(self, place_dir: Path, visit_id: str) -> FootprintVisit:
        visit_dir = place_dir / "visits" / visit_id
        metadata_path = visit_dir / "visit.json"
        thought_path = visit_dir / "thought.md"

        with metadata_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        thought = ""
        if thought_path.exists():
            thought = thought_path.read_text(encoding="utf-8")
        return FootprintVisit.from_dict(data, thought)

    def _load_legacy_place(self, place_dir: Path, data: dict[str, object]) -> FootprintPlace:
        thought = ""
        thought_path = place_dir / "thought.md"
        if thought_path.exists():
            thought = thought_path.read_text(encoding="utf-8")

        visit = FootprintVisit(
            id=f"{data.get('id', place_dir.name)}_legacy",
            date=str(data.get("date", "")),
            thought=thought,
            created_at=str(data.get("created_at", now_iso())),
            updated_at=str(data.get("updated_at", now_iso())),
            related_entry_id=str(data.get("related_entry_id", "")),
            images=[FootprintImage.from_value(item) for item in data.get("images", [])],
        )

        return FootprintPlace(
            id=str(data.get("id", place_dir.name)),
            place_name=str(data.get("place_name", "")),
            summary="",
            created_at=str(data.get("created_at", now_iso())),
            updated_at=str(data.get("updated_at", now_iso())),
            images=[],
            visits=[visit],
        )

    def _matches_query(self, place: FootprintPlace, keyword: str) -> bool:
        haystacks = [
            place.place_name,
            place.summary,
            " ".join(image.label for image in place.images if image.label),
        ]

        for visit in place.visits:
            haystacks.extend(
                [
                    visit.date,
                    visit.thought,
                    " ".join(image.label for image in visit.images if image.label),
                ],
            )

        return any(keyword in text.lower() for text in haystacks if text)

    def _sync_images(
        self,
        images_dir: Path,
        image_items: Iterable[FootprintImageDraft],
    ) -> list[FootprintImage]:
        images_dir.mkdir(parents=True, exist_ok=True)

        keep_images: list[FootprintImage] = []
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
                    FootprintImage(
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
