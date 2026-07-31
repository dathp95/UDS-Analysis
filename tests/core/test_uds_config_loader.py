import json
import tempfile
import unittest
from pathlib import Path

from core.config_loader import load_uds_config
from core import uds_lookup


class UDSConfigLoaderTests(unittest.TestCase):

    def _write_json(self, data):
        handle = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            encoding="utf-8",
            delete=False,
        )
        json.dump(data, handle)
        handle.close()
        path = Path(handle.name)
        self.addCleanup(path.unlink, missing_ok=True)
        return path

    def test_loads_schema_v2_and_merges_user_nrc(self):
        services = self._write_json({
            "schema_version": 2,
            "timeout": {"positive_response": 3},
            "services": {
                "22": {
                    "name": "Read ECU",
                    "positive_sid": "62",
                    "match": "did",
                }
            },
        })
        user = self._write_json({
            "schema_version": 2,
            "nrc": {"72": "Programming Failure"},
        })

        config = load_uds_config(services, user)

        self.assertEqual(config["timeout"]["positive_response"], 3.0)
        self.assertEqual(config["services"], {"22": "Read ECU"})
        self.assertEqual(config["positive_sid"], {"22": "62"})
        self.assertEqual(config["match_rule"], {"22": "did"})
        self.assertEqual(config["nrc"], {"72": "Programming Failure"})

    def test_falls_back_to_legacy_config_when_schema_v2_files_missing(self):
        legacy = self._write_json({
            "timeout": {"positive_response": 10},
            "services": {"10": "Session"},
            "positive_sid": {"10": "50"},
            "match_rule": {"10": "sub"},
            "nrc": {},
        })

        config = load_uds_config(
            services_path=legacy.with_name("missing-services.json"),
            user_path=legacy.with_name("missing-user.json"),
            legacy_path=legacy,
        )

        self.assertEqual(config["services"], {"10": "Session"})

    def test_reload_updates_runtime_maps_in_place(self):
        services = self._write_json({
            "schema_version": 2,
            "services": {
                "99": {
                    "name": "Custom Service",
                    "positive_sid": "D9",
                    "match": "none",
                }
            },
        })
        user = self._write_json({
            "schema_version": 2,
            "nrc": {"AB": "Custom NRC"},
        })
        old_services = dict(uds_lookup.SERVICE_NAME_MAP)
        old_nrc = dict(uds_lookup.NRC_NAME_MAP)
        self.addCleanup(uds_lookup.reload_uds_config)
        self.addCleanup(uds_lookup.SERVICE_NAME_MAP.clear)
        self.addCleanup(uds_lookup.SERVICE_NAME_MAP.update, old_services)
        self.addCleanup(uds_lookup.NRC_NAME_MAP.clear)
        self.addCleanup(uds_lookup.NRC_NAME_MAP.update, old_nrc)

        uds_lookup.reload_uds_config(services, user)

        self.assertEqual(uds_lookup.get_service_name(0x99), "Custom Service")
        self.assertEqual(uds_lookup.get_nrc_name(0xAB), "Custom NRC")
