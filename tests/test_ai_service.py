from __future__ import annotations

import json
import shutil
import sys
import unittest
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from life_dairy.ai_service import (
    AINotConfiguredError,
    AISettings,
    load_ai_settings,
    save_ai_settings,
    _mask_key,
)


class AIServiceConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case_dir = ROOT / ".tmp_testdata" / f"ai_case_{uuid4().hex}"
        self.case_dir.mkdir(parents=True, exist_ok=False)

    def tearDown(self) -> None:
        shutil.rmtree(self.case_dir, ignore_errors=True)

    def test_load_settings_returns_defaults_when_file_missing(self) -> None:
        settings = load_ai_settings(self.case_dir)
        self.assertEqual("", settings.api_key)
        self.assertEqual("https://api.deepseek.com", settings.base_url)
        self.assertEqual("deepseek-chat", settings.model)
        self.assertFalse(settings.enabled)

    def test_save_and_load_settings_roundtrip(self) -> None:
        settings = AISettings(
            api_key="sk-test-key-12345678",
            base_url="https://api.deepseek.com",
            model="deepseek-chat",
            enabled=True,
            timeout_seconds=90,
        )
        save_ai_settings(self.case_dir, settings)

        loaded = load_ai_settings(self.case_dir)
        self.assertEqual("sk-test-key-12345678", loaded.api_key)
        self.assertEqual("https://api.deepseek.com", loaded.base_url)
        self.assertEqual("deepseek-chat", loaded.model)
        self.assertTrue(loaded.enabled)
        self.assertEqual(90, loaded.timeout_seconds)

    def test_settings_file_stored_in_config_subdir(self) -> None:
        settings = AISettings(api_key="sk-test", enabled=True)
        save_ai_settings(self.case_dir, settings)

        config_file = self.case_dir / "config" / "ai_settings.json"
        self.assertTrue(config_file.exists())
        with config_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual("sk-test", data["api_key"])

    def test_disabled_setting_raises_not_configured(self) -> None:
        from life_dairy.ai_service import call_ai

        settings = AISettings(api_key="sk-test-key", enabled=False)
        save_ai_settings(self.case_dir, settings)

        with self.assertRaises(AINotConfiguredError) as ctx:
            call_ai(self.case_dir, "prompt", "test")
        self.assertIn("未启用", str(ctx.exception))

    def test_empty_api_key_raises_not_configured(self) -> None:
        from life_dairy.ai_service import call_ai

        settings = AISettings(api_key="", enabled=True)
        save_ai_settings(self.case_dir, settings)

        with self.assertRaises(AINotConfiguredError) as ctx:
            call_ai(self.case_dir, "prompt", "test")
        self.assertIn("API Key", str(ctx.exception))

    def test_mask_key_shorter_than_8(self) -> None:
        self.assertEqual("****", _mask_key("sk-123"))

    def test_mask_key_normal(self) -> None:
        masked = _mask_key("sk-abcdefghijklmnop1234")
        self.assertTrue(masked.startswith("sk-a"))
        self.assertTrue(masked.endswith("1234"))
        self.assertIn("****", masked)


if __name__ == "__main__":
    unittest.main()
