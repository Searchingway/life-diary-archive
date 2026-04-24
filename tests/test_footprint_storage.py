from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from life_dairy.footprint_storage import FootprintStorage
from life_dairy.models import FootprintImageDraft


class FootprintStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case_dir = ROOT / ".tmp_testdata" / f"footprint_case_{uuid4().hex}"
        self.case_dir.mkdir(parents=True, exist_ok=False)
        self.storage = FootprintStorage(self.case_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.case_dir, ignore_errors=True)

    def test_save_and_reload_place_with_summary_and_visit(self) -> None:
        place = self.storage.create_empty_place()
        place.place_name = "松花江畔"
        place.summary = "一个适合散步和发呆的地方。"

        visit = self.storage.create_empty_visit("2026-04-18")
        visit.thought = "那天风很大，但心情很好。"
        visit.related_entry_id = "entry-123"
        place.visits.append(visit)

        saved = self.storage.save_place(place)
        loaded = self.storage.load_place(saved.id)

        self.assertEqual("松花江畔", loaded.place_name)
        self.assertEqual("一个适合散步和发呆的地方。", loaded.summary)
        self.assertEqual(1, len(loaded.visits))
        self.assertEqual("2026-04-18", loaded.visits[0].date)
        self.assertEqual("那天风很大，但心情很好。", loaded.visits[0].thought)
        self.assertEqual("entry-123", loaded.visits[0].related_entry_id)

    def test_list_places_can_search_place_summary_visit_date_visit_thought_and_labels(self) -> None:
        place_image = self.case_dir / "place.jpg"
        visit_image = self.case_dir / "visit.jpg"
        place_image.write_bytes(b"jpeg-data")
        visit_image.write_bytes(b"jpeg-data-2")

        place = self.storage.create_empty_place()
        place.place_name = "江边公园"
        place.summary = "适合看晚霞。"
        visit = self.storage.create_empty_visit("2026-04-24")
        visit.thought = "今天在这里待了很久。"
        place.visits.append(visit)

        self.storage.save_place(
            place,
            place_image_items=[FootprintImageDraft(source_path=place_image, label="地点封面")],
            visit_image_items={visit.id: [FootprintImageDraft(source_path=visit_image, label="日落照片")]},
        )

        other = self.storage.create_empty_place()
        other.place_name = "图书馆"
        other.summary = "安静。"
        other_visit = self.storage.create_empty_visit("2026-04-23")
        other_visit.thought = "整理了两小时笔记。"
        other.visits.append(other_visit)
        self.storage.save_place(other)

        self.assertEqual(["江边公园"], [item.place_name for item in self.storage.list_places("江边")])
        self.assertEqual(["江边公园"], [item.place_name for item in self.storage.list_places("晚霞")])
        self.assertEqual(["图书馆"], [item.place_name for item in self.storage.list_places("两小时笔记")])
        self.assertEqual(["江边公园"], [item.place_name for item in self.storage.list_places("2026-04-24")])
        self.assertEqual(["江边公园"], [item.place_name for item in self.storage.list_places("地点封面")])
        self.assertEqual(["江边公园"], [item.place_name for item in self.storage.list_places("日落照片")])

    def test_list_place_visits_by_date_returns_place_and_visit_pairs(self) -> None:
        first_place = self.storage.create_empty_place()
        first_place.place_name = "早餐店"
        first_visit = self.storage.create_empty_visit("2026-04-24")
        first_place.visits.append(first_visit)
        self.storage.save_place(first_place)

        second_place = self.storage.create_empty_place()
        second_place.place_name = "植物园"
        second_visit = self.storage.create_empty_visit("2026-04-24")
        second_place.visits.append(second_visit)
        self.storage.save_place(second_place)

        items = self.storage.list_place_visits_by_date("2026-04-24")
        self.assertEqual(["早餐店", "植物园"], [place.place_name for place, _visit in items])
        self.assertEqual(["2026-04-24", "2026-04-24"], [visit.date for _place, visit in items])

    def test_delete_place_hides_item_from_active_list(self) -> None:
        place = self.storage.create_empty_place()
        saved = self.storage.save_place(place)

        self.storage.delete_place(saved.id)

        self.assertTrue(self.storage.footprint_dir(saved.id).exists())
        self.assertEqual([], self.storage.list_places())

    def test_save_and_reload_place_images_and_visit_images(self) -> None:
        place_image = self.case_dir / "place.jpg"
        visit_image_one = self.case_dir / "visit1.jpg"
        visit_image_two = self.case_dir / "visit2.png"
        place_image.write_bytes(b"jpeg-data")
        visit_image_one.write_bytes(b"jpeg-data-1")
        visit_image_two.write_bytes(b"png-data-2")

        place = self.storage.create_empty_place()
        place.place_name = "江边"
        visit = self.storage.create_empty_visit("2026-04-24")
        place.visits.append(visit)

        saved = self.storage.save_place(
            place,
            place_image_items=[FootprintImageDraft(source_path=place_image, label="地点图")],
            visit_image_items={
                visit.id: [
                    FootprintImageDraft(source_path=visit_image_one, label="白天"),
                    FootprintImageDraft(source_path=visit_image_two, label=""),
                ],
            },
        )
        loaded = self.storage.load_place(saved.id)

        self.assertEqual(1, len(loaded.images))
        self.assertEqual("地点图", loaded.images[0].label)
        self.assertEqual(1, len(loaded.visits))
        self.assertEqual(2, len(loaded.visits[0].images))
        self.assertEqual("白天", loaded.visits[0].images[0].label)
        self.assertEqual("", loaded.visits[0].images[1].label)
        self.assertTrue(self.storage.resolve_place_image_path(saved.id, loaded.images[0].file_name).exists())
        self.assertTrue(
            self.storage.resolve_visit_image_path(saved.id, loaded.visits[0].id, loaded.visits[0].images[0].file_name).exists(),
        )


if __name__ == "__main__":
    unittest.main()
