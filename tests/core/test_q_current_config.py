import json
import math
import tempfile
import unittest
from pathlib import Path

from core.q_current_config import (
    DEFAULT_Q_CURRENT_CONFIG,
    QCurrentConfig,
    load_q_current_config,
    save_q_current_config,
)


class QCurrentConfigTests(unittest.TestCase):

    def test_missing_config_returns_default_without_creating_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "q_current_config.json"

            config = load_q_current_config(config_file)

            self.assertEqual(config, DEFAULT_Q_CURRENT_CONFIG)
            self.assertFalse(config_file.exists())

    def test_save_then_reload_round_trips_global_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "q_current_config.json"
            config = QCurrentConfig(
                standard_current_ma=25.0,
                wake_up_limit_ma=250.0,
                wake_duration_s=3.0,
            )

            save_q_current_config(config, config_file)
            loaded = load_q_current_config(config_file)

            self.assertEqual(loaded, config)
            data = json.loads(config_file.read_text(encoding="utf-8"))
            self.assertEqual(data["version"], 1)
            self.assertEqual(data["standard_current_ma"], 25.0)
            self.assertEqual(data["wake_up_limit_ma"], 250.0)
            self.assertEqual(data["wake_duration_s"], 3.0)
            self.assertEqual(data["sampling_duration_enabled"], True)
            self.assertEqual(data["sampling_duration_min"], 60.0)
            self.assertFalse(config_file.with_name("q_current_config.json.tmp").exists())

    def test_malformed_json_falls_back_to_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "q_current_config.json"
            config_file.write_text("{ bad json", encoding="utf-8")

            self.assertEqual(load_q_current_config(config_file), DEFAULT_Q_CURRENT_CONFIG)
            self.assertEqual(config_file.read_text(encoding="utf-8"), "{ bad json")

    def test_invalid_json_values_fall_back_to_default(self):
        invalid_payloads = [
            {"standard_current_ma": -1, "wake_up_limit_ma": 300, "wake_duration_s": 2},
            {"standard_current_ma": 30, "wake_up_limit_ma": "ABC", "wake_duration_s": 2},
            {"standard_current_ma": 30, "wake_up_limit_ma": 300, "wake_duration_s": None},
            {"standard_current_ma": 30, "wake_up_limit_ma": 20, "wake_duration_s": 2},
            {"standard_current_ma": math.nan, "wake_up_limit_ma": 300, "wake_duration_s": 2},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "q_current_config.json"
            for payload in invalid_payloads:
                with self.subTest(payload=payload):
                    config_file.write_text(json.dumps(payload), encoding="utf-8")
                    self.assertEqual(load_q_current_config(config_file), DEFAULT_Q_CURRENT_CONFIG)

    def test_old_config_loads_sampling_duration_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "q_current_config.json"
            config_file.write_text(
                json.dumps({
                    "version": 1,
                    "standard_current_ma": 25.0,
                    "wake_up_limit_ma": 250.0,
                    "wake_duration_s": 3.0,
                }),
                encoding="utf-8",
            )

            config = load_q_current_config(config_file)

            self.assertEqual(config.standard_current_ma, 25.0)
            self.assertEqual(config.wake_up_limit_ma, 250.0)
            self.assertEqual(config.wake_duration_s, 3.0)
            self.assertTrue(config.sampling_duration_enabled)
            self.assertEqual(config.sampling_duration_min, 60.0)

    def test_save_then_reload_round_trips_sampling_duration_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "q_current_config.json"
            config = QCurrentConfig(
                standard_current_ma=25.0,
                wake_up_limit_ma=250.0,
                wake_duration_s=3.0,
                sampling_duration_enabled=False,
                sampling_duration_min=75.0,
            )

            save_q_current_config(config, config_file)
            loaded = load_q_current_config(config_file)

            self.assertEqual(loaded, config)
            data = json.loads(config_file.read_text(encoding="utf-8"))
            self.assertFalse(data["sampling_duration_enabled"])
            self.assertEqual(data["sampling_duration_min"], 75.0)

    def test_invalid_sampling_duration_values_fall_back_without_losing_other_config(self):
        invalid_payloads = [
            {"sampling_duration_enabled": "yes", "sampling_duration_min": 90},
            {"sampling_duration_enabled": True, "sampling_duration_min": 0},
            {"sampling_duration_enabled": False, "sampling_duration_min": "ABC"},
            {"sampling_duration_enabled": True, "sampling_duration_min": math.nan},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "q_current_config.json"
            for payload in invalid_payloads:
                with self.subTest(payload=payload):
                    config_file.write_text(
                        json.dumps({
                            "standard_current_ma": 25,
                            "wake_up_limit_ma": 250,
                            "wake_duration_s": 3,
                            **payload,
                        }),
                        encoding="utf-8",
                    )
                    config = load_q_current_config(config_file)
                    self.assertEqual(config.standard_current_ma, 25.0)
                    self.assertEqual(config.wake_up_limit_ma, 250.0)
                    self.assertEqual(config.wake_duration_s, 3.0)
                    self.assertTrue(config.sampling_duration_enabled)
                    self.assertEqual(config.sampling_duration_min, 60.0)

    def test_save_rejects_invalid_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "q_current_config.json"
            with self.assertRaises(ValueError):
                save_q_current_config(
                    QCurrentConfig(
                        standard_current_ma=300.0,
                        wake_up_limit_ma=30.0,
                        wake_duration_s=2.0,
                    ),
                    config_file,
                )
            self.assertFalse(config_file.exists())


if __name__ == "__main__":
    unittest.main()