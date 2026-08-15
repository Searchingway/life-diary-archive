import json
import os
import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "diary_v2.0"))
from data_root_config import DataRootError, migrate_data_root, resolve_data_root  # noqa: E402


class DataRootConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.default = self.root / "default" / "Diary"
        self.bootstrap = self.root / "bootstrap.json"
        self.previous = os.environ.pop("LIFE_DIARY_DATA_ROOT", None)

    def tearDown(self) -> None:
        if self.previous is not None:
            os.environ["LIFE_DIARY_DATA_ROOT"] = self.previous
        self.temp.cleanup()

    def test_default_is_used_without_bootstrap(self) -> None:
        self.assertEqual(self.default.resolve(), resolve_data_root(self.default, self.bootstrap))

    def test_bootstrap_root_is_used_when_present(self) -> None:
        selected = self.root / "selected"
        self.bootstrap.write_text(json.dumps({"data_root": str(selected)}), encoding="utf-8")
        self.assertEqual(selected.resolve(), resolve_data_root(self.default, self.bootstrap))

    def test_environment_has_priority_over_bootstrap(self) -> None:
        os.environ["LIFE_DIARY_DATA_ROOT"] = str(self.root / "environment")
        self.bootstrap.write_text(json.dumps({"data_root": str(self.root / "selected")}), encoding="utf-8")
        self.assertEqual((self.root / "environment").resolve(), resolve_data_root(self.default, self.bootstrap))

    def test_invalid_bootstrap_root_falls_back_to_default(self) -> None:
        self.bootstrap.write_text("not json", encoding="utf-8")
        self.assertEqual(self.default.resolve(), resolve_data_root(self.default, self.bootstrap))

    def test_destination_existing_is_not_overwritten_and_bootstrap_is_unchanged(self) -> None:
        source = self.root / "source"
        (source / "entries" / "entry").mkdir(parents=True)
        (source / "entries" / "entry" / "entry.json").write_text("{}", encoding="utf-8")
        destination = self.root / "destination"
        destination.mkdir()
        self.bootstrap.write_text(json.dumps({"data_root": str(source)}), encoding="utf-8")
        previous = self.bootstrap.read_text(encoding="utf-8")
        with self.assertRaises(DataRootError):
            migrate_data_root(source, destination, self.bootstrap)
        self.assertEqual(previous, self.bootstrap.read_text(encoding="utf-8"))
        self.assertTrue((source / "entries" / "entry" / "entry.json").exists())

    def test_failed_copy_does_not_change_bootstrap_or_source(self) -> None:
        source = self.root / "source"
        source.mkdir()
        (source / "marker.txt").write_text("keep", encoding="utf-8")
        destination = self.root / "missing" / "destination"
        self.bootstrap.write_text(json.dumps({"data_root": str(source)}), encoding="utf-8")
        previous = self.bootstrap.read_text(encoding="utf-8")
        with self.assertRaises(DataRootError):
            migrate_data_root(source, destination, self.bootstrap, copier=lambda *_: (_ for _ in ()).throw(OSError("copy failed")))
        self.assertEqual(previous, self.bootstrap.read_text(encoding="utf-8"))
        self.assertEqual("keep", (source / "marker.txt").read_text(encoding="utf-8"))
