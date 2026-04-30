from __future__ import annotations

import json
import shutil
import sys
import unittest
import zipfile
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from life_dairy.backup_service import create_backup, restore_backup, validate_backup
from life_dairy.book_storage import BookStorage
from life_dairy.footprint_storage import FootprintStorage
from life_dairy.lesson_storage import LessonStorage
from life_dairy.plan_storage import PlanStorage
from life_dairy.storage import DiaryStorage


class BackupServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case_dir = ROOT / ".tmp_testdata" / f"backup_case_{uuid4().hex}"
        self.data_root = self.case_dir / "Diary"
        self.backup_dir = self.case_dir / "backups"
        self.case_dir.mkdir(parents=True, exist_ok=False)
        self.diary_storage = DiaryStorage(self.data_root)
        self.footprint_storage = FootprintStorage(self.data_root)
        self.book_storage = BookStorage(self.data_root)
        self.plan_storage = PlanStorage(self.data_root)
        self.lesson_storage = LessonStorage(self.data_root)

    def tearDown(self) -> None:
        shutil.rmtree(self.case_dir, ignore_errors=True)

    def test_create_backup_contains_manifest_diary_and_module_dirs(self) -> None:
        entry = self.diary_storage.create_empty_entry()
        entry.title = "备份测试"
        self.diary_storage.save_entry(entry)

        zip_path = create_backup(self.data_root, self.backup_dir, "2.5")

        self.assertTrue(zip_path.exists())
        with zipfile.ZipFile(zip_path, "r") as archive:
            names = archive.namelist()
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))

        self.assertEqual("LifeDiaryBackup", manifest["backup_type"])
        self.assertEqual("2.5", manifest["app_version"])
        self.assertIn("manifest.json", names)
        self.assertIn("Diary/", names)
        self.assertTrue(any(name.startswith("Diary/entries/") for name in names))
        self.assertTrue(any(name.startswith("Diary/footprints/") for name in names))
        self.assertTrue(any(name.startswith("Diary/books/") for name in names))
        self.assertTrue(any(name.startswith("Diary/plans/") for name in names))
        self.assertTrue(any(name.startswith("Diary/lessons/") for name in names))

    def test_validate_backup_accepts_legal_backup(self) -> None:
        zip_path = create_backup(self.data_root, self.backup_dir, "2.5")

        valid, message = validate_backup(zip_path)

        self.assertTrue(valid, message)

    def test_validate_backup_rejects_invalid_zip(self) -> None:
        bad_zip = self.case_dir / "bad.zip"
        bad_zip.write_text("not a zip", encoding="utf-8")

        valid, message = validate_backup(bad_zip)

        self.assertFalse(valid)
        self.assertIn("zip", message.lower())

    def test_validate_backup_rejects_zip_without_manifest(self) -> None:
        no_manifest = self.case_dir / "no_manifest.zip"
        with zipfile.ZipFile(no_manifest, "w") as archive:
            archive.writestr("Diary/entries/", "")

        valid, message = validate_backup(no_manifest)

        self.assertFalse(valid)
        self.assertIn("manifest", message)

    def test_restore_backup_creates_before_restore_backup_and_restores_data(self) -> None:
        original = self.diary_storage.create_empty_entry()
        original.title = "恢复前"
        self.diary_storage.save_entry(original)
        source_backup = create_backup(self.data_root, self.backup_dir, "2.5")

        replacement_root = self.case_dir / "ReplacementDiary"
        replacement_storage = DiaryStorage(replacement_root)
        FootprintStorage(replacement_root)
        BookStorage(replacement_root)
        PlanStorage(replacement_root)
        LessonStorage(replacement_root)
        replacement = replacement_storage.create_empty_entry()
        replacement.title = "恢复后"
        replacement_storage.save_entry(replacement)
        replacement_backup = create_backup(replacement_root, self.backup_dir, "2.5")

        safety_path = restore_backup(replacement_backup, self.data_root, self.backup_dir, "2.5")
        restored_storage = DiaryStorage(self.data_root)
        restored_titles = [item.title for item in restored_storage.list_entries()]

        self.assertTrue(safety_path.exists())
        self.assertTrue(safety_path.name.startswith("BeforeRestoreBackup_"))
        self.assertEqual(["恢复后"], restored_titles)
        self.assertTrue(validate_backup(safety_path)[0])
        self.assertTrue(validate_backup(source_backup)[0])

    def test_restore_invalid_backup_does_not_overwrite_current_data(self) -> None:
        entry = self.diary_storage.create_empty_entry()
        entry.title = "不能被覆盖"
        self.diary_storage.save_entry(entry)
        bad_zip = self.case_dir / "bad.zip"
        bad_zip.write_text("not a zip", encoding="utf-8")

        with self.assertRaises(ValueError):
            restore_backup(bad_zip, self.data_root, self.backup_dir, "2.5")

        loaded = DiaryStorage(self.data_root).list_entries()
        self.assertEqual(["不能被覆盖"], [item.title for item in loaded])
        self.assertFalse(any(self.backup_dir.glob("BeforeRestoreBackup_*.zip")))


if __name__ == "__main__":
    unittest.main()
