from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "diary_v2.0"
if str(V2) not in sys.path:
    sys.path.insert(0, str(V2))

import data_api
from plan_v2 import migrate_plan_to_v2
from sync_service import SyncService


class SyncProtocolV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.original_data_root = data_api.DATA_ROOT
        data_api.DATA_ROOT = self.root / "Diary"
        self.service = SyncService()

    def tearDown(self) -> None:
        data_api.DATA_ROOT = self.original_data_root
        self.temp_dir.cleanup()

    def test_plan_v1_migration_is_lossless_and_idempotent(self) -> None:
        legacy = {
            "id": "plan_1",
            "title": "Read",
            "goal": "Finish a book",
            "startDate": "2026-08-01",
            "deadline": "2026-08-31",
            "status": "暂停",
            "priority": "普通",
            "note": "Keep notes",
            "tags": ["reading"],
            "tasks": [{"id": "task_1", "title": "Chapter 1", "date": "2026-08-02", "done": True, "note": "done"}],
            "plan_type": "subtract",
            "subtract_mode": "不做",
            "trigger_scene": "evening",
            "avoid_behavior": "scrolling",
            "reason": "sleep",
            "alternative_action": "read",
            "created_at": "2026-08-01T00:00:00+08:00",
            "updated_at": "2026-08-02T00:00:00+08:00",
            "custom_mobile_field": "preserved",
        }
        migrated = migrate_plan_to_v2(legacy)
        self.assertEqual(2, migrated["schema_version"])
        self.assertEqual("2026-08-31", migrated["due_date"])
        self.assertEqual("2026-08-02", migrated["tasks"][0]["scheduled_date"])
        self.assertEqual("已暂停", migrated["status"])
        self.assertEqual("中", migrated["priority"])
        self.assertEqual("preserved", migrated["custom_mobile_field"])
        self.assertEqual(migrated, migrate_plan_to_v2(migrated))

    def test_desktop_plan_save_upgrades_v1_and_reads_shared_fixture(self) -> None:
        fixture_path = ROOT / "shared" / "sync" / "fixtures" / "plan_v2_full.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        saved = data_api.save_generic_record(
            "plans",
            {"id": "desktop_plan", "title": "Desktop plan", "body": "notes", "extra": {"deadline": "2026-08-15", "status": "暂停", "priority": "普通", "tasks": [{"title": "Task", "date": "2026-08-12"}]}},
        )
        self.assertEqual(2, saved["extra"]["schema_version"])
        self.assertEqual("2026-08-15", saved["extra"]["due_date"])
        self.assertEqual("已暂停", saved["extra"]["status"])
        self.assertEqual("中", saved["extra"]["priority"])
        self.assertEqual("2026-08-12", saved["extra"]["tasks"][0]["scheduled_date"])
        self.assertEqual(fixture, migrate_plan_to_v2(fixture))

    def test_same_id_mobile_subset_is_stale_and_cannot_mutate_desktop_until_commit(self) -> None:
        data_api.save_entry({"id": "same_id", "date": "2026-08-03", "title": "Library", "body": "A\nB\nC"})
        package = self._mobile_zip(
            {
                "Diary/entries/same_id/entry.json": json.dumps({"id": "same_id", "date": "2026-08-03", "title": "Library", "images": []}),
                "Diary/entries/same_id/content.md": "A\nB",
            }
        )

        session = self.service.prepare_mobile_import(package)

        self.assertEqual(1, session["summary"]["stale_mobile"])
        self.assertEqual("A\nB\nC", data_api.list_module_records("entries")[0]["body"])
        self.assertTrue(Path(session["safety_backup"]).exists())
        self.assertTrue(self.service.commit_import(session["id"])["ok"])
        self.assertEqual("A\nB\nC", data_api.list_module_records("entries")[0]["body"])

    def test_different_date_is_new_and_crlf_text_is_not_a_false_conflict(self) -> None:
        data_api.save_entry({"id": "same_text", "date": "2026-08-01", "title": "Title", "body": "A\nB\n"})
        package = self._mobile_zip(
            {
                "Diary/entries/same_text/entry.json": json.dumps({"id": "same_text", "date": "2026-08-01", "title": "Title", "images": []}),
                "Diary/entries/same_text/content.md": "A\r\nB   \r\n",
                "Diary/entries/new_date/entry.json": json.dumps({"id": "new_date", "date": "2026-08-02", "title": "New", "images": []}),
                "Diary/entries/new_date/content.md": "New body",
            }
        )
        session = self.service.prepare_mobile_import(package)
        self.assertEqual(1, session["summary"]["unchanged"])
        self.assertEqual(1, session["summary"]["new"])
        self.service.commit_import(session["id"])
        self.assertEqual({"same_text", "new_date"}, {item["id"] for item in data_api.list_module_records("entries")})

    def test_same_date_different_id_identical_content_is_duplicate(self) -> None:
        data_api.save_entry({"id": "pc_id", "date": "2026-08-03", "title": "Title", "body": "Same"})
        package = self._mobile_zip(
            {
                "Diary/entries/mobile_id/entry.json": json.dumps({"id": "mobile_id", "date": "2026-08-03", "title": "Title", "images": []}),
                "Diary/entries/mobile_id/content.md": "Same",
            }
        )
        session = self.service.prepare_mobile_import(package)
        self.assertEqual(1, session["summary"]["duplicate"])
        self.service.commit_import(session["id"])
        self.assertEqual(["pc_id"], [item["id"] for item in data_api.list_module_records("entries")])

    def test_new_mobile_image_on_same_id_is_a_conflict(self) -> None:
        data_api.save_entry({"id": "same_id", "date": "2026-08-03", "title": "Title", "body": "Same"})
        package = self._mobile_zip(
            {
                "Diary/entries/same_id/entry.json": json.dumps({"id": "same_id", "date": "2026-08-03", "title": "Title", "images": [{"file_name": "new.png"}]}),
                "Diary/entries/same_id/content.md": "Same",
                "Diary/entries/same_id/images/new.png": b"new image",
            }
        )
        self.assertEqual(1, self.service.prepare_mobile_import(package)["summary"]["conflict"])

    def test_preflight_rejects_zip_path_traversal(self) -> None:
        package = self.root / "unsafe.zip"
        with zipfile.ZipFile(package, "w") as archive:
            archive.writestr("manifest.json", json.dumps({"app": "LifeDiary", "protocol_version": 1, "package_role": "mobile_snapshot", "source_platform": "mobile"}))
            archive.writestr("../escape.txt", "no")
        with self.assertRaisesRegex(ValueError, "unsafe ZIP path"):
            self.service.prepare_mobile_import(package)

    def test_conflict_requires_resolution_keeps_pc_id_and_unions_images(self) -> None:
        desktop = data_api.save_entry({"id": "pc_id", "date": "2026-08-03", "title": "Library", "body": "PC text"})
        data_api.add_entry_images("pc_id", {"files": [{"name": "pc.png", "data": "cGM="}]})
        package = self._mobile_zip(
            {
                "Diary/entries/mobile_id/entry.json": json.dumps({"id": "mobile_id", "date": "2026-08-03", "title": "Library", "images": [{"file_name": "mobile.png"}]}),
                "Diary/entries/mobile_id/content.md": "Mobile text",
                "Diary/entries/mobile_id/images/mobile.png": b"mobile",
            }
        )
        session = self.service.prepare_mobile_import(package)
        conflict = session["conflicts"][0]

        self.assertEqual("conflict", conflict["kind"])
        self.assertEqual("pc_id", conflict["canonical_id"])
        with self.assertRaisesRegex(ValueError, "unresolved"):
            self.service.commit_import(session["id"])
        resolved = self.service.resolve_entry_conflict(session["id"], conflict["id"], "Merged text")
        self.assertEqual("pc_id", resolved["canonical_id"])
        self.service.commit_import(session["id"])
        record = data_api.list_module_records("entries")[0]
        self.assertEqual("pc_id", record["id"])
        self.assertEqual("Merged text", record["body"])
        self.assertEqual({"pc.png", "mobile.png"}, {image["file_name"] for image in record["extra"]["images"]})

    def test_canonical_zip_contains_only_shared_modules_and_v1_manifest(self) -> None:
        data_api.save_entry({"id": "entry_1", "date": "2026-08-01", "title": "Entry", "body": "Body"})
        data_api.save_generic_record("thoughts", {"id": "desktop_only", "title": "Private", "body": "No sync"})
        output = self.service.create_desktop_canonical_zip(self.root / "canonical.zip")
        with zipfile.ZipFile(output) as archive:
            manifest = json.loads(archive.read("manifest.json"))
            names = archive.namelist()
        self.assertEqual("desktop_canonical", manifest["package_role"])
        self.assertEqual(1, manifest["protocol_version"])
        self.assertIn("Diary/entries/entry_1/entry.json", names)
        self.assertFalse(any("desktop_only" in name or "/thoughts/" in name for name in names))

    def _mobile_zip(self, files: dict[str, str | bytes]) -> Path:
        package = self.root / "mobile.zip"
        with zipfile.ZipFile(package, "w") as archive:
            archive.writestr(
                "manifest.json",
                json.dumps(
                    {
                        "app": "LifeDiary",
                        "protocol_version": 1,
                        "package_role": "mobile_snapshot",
                        "source_platform": "mobile",
                        "created_at": "2026-08-10T00:00:00+08:00",
                        "schema_versions": {"plans": 2},
                    }
                ),
            )
            for name, content in files.items():
                archive.writestr(name, content)
        return package


if __name__ == "__main__":
    unittest.main()
