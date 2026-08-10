from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "diary_v2.0"
if str(V2) not in sys.path:
    sys.path.insert(0, str(V2))

import data_api
from plan_v2 import migrate_plan_to_v2
from sync_service import SyncService
from src.life_dairy.backup_service import restore_backup, validate_backup


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

    def test_plan_migration_removes_known_aliases_and_normalises_all_accepted_values(self) -> None:
        migrated = migrate_plan_to_v2(
            {
                "id": "alias_plan",
                "startDate": "2026-08-01",
                "deadline": "2026-08-31",
                "note": "canonical notes",
                "status": "搁置",
                "priority": "普通",
                "plan_type": "reduce",
                "unknown_extension": {"preserve": True},
                "tasks": [{"id": "one", "title": "Task", "scheduledDate": "2026-08-03", "date": "legacy"}],
            }
        )

        self.assertEqual("已暂停", migrated["status"])
        self.assertEqual("中", migrated["priority"])
        self.assertEqual("subtract", migrated["plan_type"])
        self.assertEqual("2026-08-01", migrated["start_date"])
        self.assertEqual("2026-08-31", migrated["due_date"])
        self.assertEqual("canonical notes", migrated["notes"])
        self.assertEqual("2026-08-03", migrated["tasks"][0]["scheduled_date"])
        self.assertNotIn("startDate", migrated)
        self.assertNotIn("deadline", migrated)
        self.assertNotIn("note", migrated)
        self.assertNotIn("scheduledDate", migrated["tasks"][0])
        self.assertNotIn("date", migrated["tasks"][0])
        self.assertEqual({"preserve": True}, migrated["unknown_extension"])
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

    def test_entry_conflict_preserves_labels_titles_and_a_non_lossy_merge_candidate(self) -> None:
        data_api.save_entry({"id": "entry", "date": "2026-08-03", "title": "PC title", "body": "common\nPC only\nend"})
        data_api.add_entry_images("entry", {"files": [{"name": "shared.png", "data": "c2hhcmVk", "label": "Desktop label"}, {"name": "blank.png", "data": "Ymxhbms=", "label": ""}]})
        package = self._mobile_zip(
            {
                "Diary/entries/entry/entry.json": json.dumps({"id": "entry", "date": "2026-08-03", "title": "Mobile title", "images": [{"file_name": "shared.png", "label": "Mobile label"}, {"file_name": "blank.png", "label": "Mobile fallback"}, {"file_name": "mobile.png", "label": "Mobile only"}]}),
                "Diary/entries/entry/content.md": "common\nMobile only\nend",
                "Diary/entries/entry/images/shared.png": b"shared",
                "Diary/entries/entry/images/blank.png": b"blank",
                "Diary/entries/entry/images/mobile.png": b"mobile",
            }
        )
        session = self.service.prepare_mobile_import(package)
        conflict = session["conflicts"][0]

        self.assertIn("PC only", conflict["merge_candidate"])
        self.assertIn("Mobile only", conflict["merge_candidate"])
        self.assertEqual(1, conflict["merge_candidate"].count("common"))
        self.assertEqual("PC title", conflict["desktop"]["title"])
        self.assertEqual("Mobile title", conflict["mobile"]["title"])
        self.service.resolve_entry_conflict(session["id"], conflict["id"], "Merged", "Final title")
        self.service.commit_import(session["id"])
        record = data_api.list_module_records("entries")[0]
        self.assertEqual("Final title", record["title"])
        labels = {image["file_name"]: image["label"] for image in record["extra"]["images"]}
        self.assertEqual("Desktop label", labels["shared.png"])
        self.assertEqual("Mobile fallback", labels["blank.png"])
        self.assertEqual("Mobile only", labels["mobile.png"])

    def test_footprint_auxiliary_content_difference_is_a_conflict(self) -> None:
        data_api.save_generic_record("footprints", {"id": "place", "title": "Place", "body": "same", "date": "2026-08-03"})
        record_dir = data_api.DATA_ROOT / "footprints" / "place"
        (record_dir / "summary.md").write_text("Desktop summary", encoding="utf-8")
        visit_dir = record_dir / "visits" / "visit-1"
        visit_dir.mkdir(parents=True)
        data_api.write_json(visit_dir / "visit.json", {"id": "visit-1", "date": "2026-08-03"})
        (visit_dir / "thought.md").write_text("same thought", encoding="utf-8")
        (visit_dir / "images").mkdir()
        (visit_dir / "images" / "visit.png").write_bytes(b"visit")
        (record_dir / "images").mkdir()
        (record_dir / "images" / "place.png").write_bytes(b"place")
        footprint = data_api.read_json(record_dir / "footprint.json")
        package = self._mobile_zip(
            {
                "Diary/footprints/place/footprint.json": json.dumps(footprint),
                "Diary/footprints/place/summary.md": "Mobile summary",
                "Diary/footprints/place/visits/visit-1/visit.json": json.dumps({"id": "visit-1", "date": "2026-08-03"}),
                "Diary/footprints/place/visits/visit-1/thought.md": "same thought",
                "Diary/footprints/place/visits/visit-1/images/visit.png": b"visit",
                "Diary/footprints/place/images/place.png": b"place",
            }
        )

        self.assertEqual(1, self.service.prepare_mobile_import(package)["summary"]["conflict"])

    def test_import_safety_backup_is_official_and_restorable(self) -> None:
        data_api.save_entry({"id": "before", "date": "2026-08-03", "title": "Before", "body": "saved"})
        session = self.service.prepare_mobile_import(self._mobile_zip({}))
        backup = Path(session["safety_backup"])

        self.assertTrue(validate_backup(backup)[0])
        restore_root = self.root / "restore" / "Diary"
        restore_root.mkdir(parents=True)
        data_api.DATA_ROOT = restore_root
        data_api.save_entry({"id": "other", "date": "2026-08-04", "title": "Other", "body": "replace"})
        restore_backup(backup, restore_root, self.root / "restore_backups")
        self.assertEqual(["before"], [item["id"] for item in data_api.list_module_records("entries")])

    def test_commit_cleans_bulky_session_content_but_keeps_metadata(self) -> None:
        package = self._mobile_zip(
            {
                "Diary/entries/new/entry.json": json.dumps({"id": "new", "date": "2026-08-03", "title": "New", "images": []}),
                "Diary/entries/new/content.md": "new body",
            }
        )
        session = self.service.prepare_mobile_import(package)
        session_dir = Path(self.service._session(session["id"])["session_dir"])
        self.assertTrue((session_dir / "mobile_snapshot").exists())

        self.service.commit_import(session["id"])

        self.assertFalse((session_dir / "mobile_snapshot").exists())
        self.assertFalse((session_dir / "pre_commit_data").exists())
        self.assertFalse((session_dir / "commit_data").exists())
        self.assertTrue((session_dir / "session.json").exists())

    def test_commit_swap_serializes_with_ordinary_data_mutation_lock(self) -> None:
        session = self.service.prepare_mobile_import(
            self._mobile_zip(
                {
                    "Diary/entries/new/entry.json": json.dumps({"id": "new", "date": "2026-08-03", "title": "New", "images": []}),
                    "Diary/entries/new/content.md": "new body",
                }
            )
        )
        swap_started = threading.Event()
        allow_swap = threading.Event()
        writer_finished = threading.Event()
        original_replace = __import__("sync_service").os.replace

        def paused_replace(source: str | Path, target: str | Path) -> None:
            swap_started.set()
            self.assertTrue(allow_swap.wait(3))
            original_replace(source, target)

        def ordinary_write() -> None:
            with data_api.data_mutation_lock():
                data_api.save_entry({"id": "ordinary", "date": "2026-08-04", "title": "Ordinary", "body": "write"})
            writer_finished.set()

        with patch("sync_service.os.replace", side_effect=paused_replace):
            commit_thread = threading.Thread(target=lambda: self.service.commit_import(session["id"]))
            commit_thread.start()
            self.assertTrue(swap_started.wait(3))
            writer = threading.Thread(target=ordinary_write)
            writer.start()
            self.assertFalse(writer_finished.wait(0.15))
            allow_swap.set()
            commit_thread.join(3)
            writer.join(3)
        self.assertFalse(commit_thread.is_alive())
        self.assertTrue(writer_finished.is_set())

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
