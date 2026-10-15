from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "diary_v2.0"))
import ai_config_api
import data_api
import server


class AIConfigurationTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary_root = ROOT / ".tmp_testdata"
        temporary_root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=temporary_root)
        self.root_patch = patch.object(data_api, "DATA_ROOT", Path(self.temp.name))
        self.root_patch.start()

    def tearDown(self) -> None:
        self.root_patch.stop()
        self.temp.cleanup()

    def configure(self) -> dict:
        return ai_config_api.save_configuration({"api_key": "unit-test-secret-value", "enabled": True})

    def test_settings_response_does_not_return_secret(self) -> None:
        saved = self.configure()
        self.assertTrue(saved["has_api_key"])
        self.assertNotIn("api_key", saved)
        self.assertNotIn("unit-test-secret-value", json.dumps(ai_config_api.read_configuration()))

    def test_omitted_key_is_preserved_and_explicit_clear_is_supported(self) -> None:
        self.configure()
        ai_config_api.save_configuration({"model": "other-model"})
        path = data_api.DATA_ROOT / "config" / "ai_settings.json"
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["api_key"], "unit-test-secret-value")
        cleared = ai_config_api.save_configuration({"api_key": "", "enabled": False})
        self.assertFalse(cleared["has_api_key"])
        self.assertFalse(cleared["enabled"])

    def test_invalid_configuration_does_not_replace_saved_configuration(self) -> None:
        self.configure()
        path = data_api.DATA_ROOT / "config" / "ai_settings.json"
        before = path.read_bytes()
        for payload in ({"timeout_seconds": 0}, {"timeout_seconds": True}, {"timeout_seconds": 1.5}, {"base_url": "file:///tmp"}, {"model": ""}, {"enabled": "true"}, {"api_key": "", "enabled": True}):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    ai_config_api.save_configuration(payload)
                self.assertEqual(path.read_bytes(), before)

    def test_failed_atomic_save_preserves_existing_configuration(self) -> None:
        self.configure()
        path = data_api.DATA_ROOT / "config" / "ai_settings.json"
        before = path.read_bytes()
        with patch.object(data_api, "atomic_write_json", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                ai_config_api.save_configuration({"model": "new-model"})
        self.assertEqual(path.read_bytes(), before)

    def test_saved_key_is_not_reused_for_a_different_provider(self) -> None:
        self.configure()
        for operation in (ai_config_api.save_configuration, ai_config_api.test_configuration):
            with self.subTest(operation=operation.__name__):
                with self.assertRaises(ValueError):
                    operation({"base_url": "https://other-provider.invalid/v1"})

    def test_connection_uses_unsaved_draft_without_changing_configuration(self) -> None:
        self.configure()
        path = data_api.DATA_ROOT / "config" / "ai_settings.json"
        before = path.read_bytes()
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="连接成功"))]))))
        with patch.object(ai_config_api, "_build_deepseek_client", return_value=client) as build:
            result = ai_config_api.test_configuration({"model": "draft-model", "api_key": "draft-secret-value", "enabled": False})
        self.assertTrue(result["ok"])
        self.assertEqual(build.call_args.args[0].model, "draft-model")
        self.assertEqual(build.call_args.args[0].api_key, "draft-secret-value")
        self.assertEqual(path.read_bytes(), before)

    def test_provider_failure_and_empty_response_do_not_report_success_or_leak_secret(self) -> None:
        self.configure()
        with patch.object(ai_config_api, "_build_deepseek_client", side_effect=RuntimeError("unit-test-secret-value")):
            with self.assertRaises(RuntimeError) as error:
                ai_config_api.test_configuration({})
        self.assertNotIn("unit-test-secret-value", str(error.exception))
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(choices=[]))))
        with patch.object(ai_config_api, "_build_deepseek_client", return_value=client):
            with self.assertRaises(RuntimeError):
                ai_config_api.test_configuration({})

    def test_network_wait_does_not_hold_the_global_data_mutation_lock(self) -> None:
        self.configure()
        started, release = threading.Event(), threading.Event()
        errors = []

        def create(**kwargs):
            started.set()
            release.wait(3)
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="OK"))])

        def test_connection():
            try:
                ai_config_api.test_configuration({})
            except Exception as error:
                errors.append(error)

        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        with patch.object(ai_config_api, "_build_deepseek_client", return_value=client):
            thread = threading.Thread(target=test_connection)
            thread.start()
            try:
                self.assertTrue(started.wait(2))
                acquired = data_api.data_mutation_lock().acquire(timeout=0.2)
                if acquired:
                    data_api.data_mutation_lock().release()
                self.assertTrue(acquired, "AI provider wait must not block diary saves")
            finally:
                release.set()
                thread.join()
        self.assertFalse(errors)

    def test_http_routes_save_load_and_reject_invalid_input(self) -> None:
        http_server = ThreadingHTTPServer(("127.0.0.1", 0), server.LifeDiaryHandler)
        thread = threading.Thread(target=http_server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{http_server.server_port}"
        try:
            request = Request(base + "/api/ai/settings", json.dumps({"api_key": "http-test-secret", "enabled": True}).encode(), {"Content-Type": "application/json"})
            with urlopen(request) as response:
                self.assertTrue(json.load(response)["has_api_key"])
            with urlopen(base + "/api/ai/settings") as response:
                self.assertNotIn("http-test-secret", response.read().decode())
            invalid = Request(base + "/api/ai/settings", b'{"timeout_seconds":0}', {"Content-Type": "application/json"})
            with self.assertRaises(HTTPError) as error:
                urlopen(invalid)
            self.assertEqual(error.exception.code, 400)
            self.assertIn("error", json.loads(error.exception.read().decode()))
            failed_test = Request(base + "/api/ai/test", b'{}', {"Content-Type": "application/json"})
            with patch.object(ai_config_api, "_build_deepseek_client", side_effect=RuntimeError("http-test-secret")):
                with self.assertRaises(HTTPError) as test_error:
                    urlopen(failed_test)
            self.assertEqual(test_error.exception.code, 502)
            self.assertNotIn("http-test-secret", test_error.exception.read().decode())
            config_path = data_api.DATA_ROOT / "config" / "ai_settings.json"
            before = config_path.read_bytes()
            for endpoint in ("/api/ai/settings", "/api/ai/test"):
                with self.subTest(endpoint=endpoint):
                    cross_origin = Request(base + endpoint, b'{"base_url":"https://attacker.invalid"}', {"Content-Type": "text/plain", "Origin": "https://attacker.invalid"})
                    with patch.object(ai_config_api, "_build_deepseek_client", side_effect=RuntimeError("must not connect")) as build:
                        with self.assertRaises(HTTPError) as blocked:
                            urlopen(cross_origin)
                        self.assertEqual(blocked.exception.code, 403)
                        build.assert_not_called()
                    self.assertEqual(config_path.read_bytes(), before)
            for headers, status in (
                ({"Content-Type": "text/plain"}, 415),
                ({"Content-Type": "application/json", "Origin": "https://attacker.invalid"}, 403),
                ({"Content-Type": "application/json", "Origin": "null"}, 403),
                ({"Content-Type": "application/json", "Host": "attacker.invalid", "Origin": "http://attacker.invalid"}, 403),
            ):
                with self.subTest(headers=headers):
                    request = Request(base + "/api/ai/test", b'{}', headers)
                    with self.assertRaises(HTTPError) as blocked:
                        urlopen(request)
                    self.assertEqual(blocked.exception.code, status)
            client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="OK"))]))))
            with patch.object(ai_config_api, "_build_deepseek_client", return_value=client):
                same_origin = Request(base + "/api/ai/test", b'{}', {"Content-Type": "application/json; charset=utf-8", "Origin": base})
                with urlopen(same_origin) as response:
                    self.assertTrue(json.load(response)["ok"])
        finally:
            http_server.shutdown()
            http_server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
