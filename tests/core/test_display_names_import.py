import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.config_loader import (
    MAX_DISPLAY_NAMES_FILE_SIZE,
    import_display_names,
    import_display_name_rules,
)
from core import uds_lookup


class DisplayNamesImportTests(unittest.TestCase):

    def _temp_path(self, suffix=".json"):
        handle = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        handle.close()
        path = Path(handle.name)
        self.addCleanup(path.unlink, missing_ok=True)
        return path

    def _write_json(self, data):
        path = self._temp_path()
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_imports_valid_mapping_to_destination(self):
        source = self._write_json({"22 F1 90": {"display_name": "Read VIN"}})
        destination = self._temp_path()

        result = import_display_names(source, destination)

        self.assertEqual(result["22 F1 90"]["display_name"], "Read VIN")
        self.assertEqual(json.loads(destination.read_text(encoding="utf-8")), result)

    def test_rejects_invalid_mapping_without_overwriting_destination(self):
        source = self._write_json({"22 F1 90": "Read VIN"})
        destination = self._temp_path()
        destination.write_text('{"old": {"display_name": "Keep"}}', encoding="utf-8")

        with self.assertRaises(ValueError):
            import_display_names(source, destination)

        self.assertEqual(
            json.loads(destination.read_text(encoding="utf-8")),
            {"old": {"display_name": "Keep"}},
        )

    def test_reload_display_names_updates_runtime_lookup(self):
        mapping = {"22 F1 90": {"display_name": "VIN from import"}}
        original_names = uds_lookup.UDS_DISPLAY_NAMES
        original_map = uds_lookup.DISPLAY_NAME_MAP
        self.addCleanup(setattr, uds_lookup, "UDS_DISPLAY_NAMES", original_names)
        self.addCleanup(setattr, uds_lookup, "DISPLAY_NAME_MAP", original_map)

        with patch.object(uds_lookup, "load_display_names", return_value=mapping):
            uds_lookup.reload_display_names()

        self.assertEqual(
            uds_lookup.get_display_name("22 F1 90 01"),
            "VIN from import",
        )

    def test_rejects_display_names_file_over_size_limit(self):
        source = self._temp_path()
        source.write_bytes(b"0" * (MAX_DISPLAY_NAMES_FILE_SIZE + 1))
        destination = self._temp_path()

        with self.assertRaises(ValueError):
            import_display_names(source, destination)

    def test_imports_rules_and_normalizes_payload_spacing(self):
        destination = self._write_json(
            {"22 F1 20": {"display_name": "Old Global Time"}}
        )

        result = import_display_name_rules(
            "22 F1 20| Global Time\n"
            "22 F1 22 | Vehicle   supply Voltage\n"
            "22 D1 00   | Key Sw Number",
            destination,
        )

        self.assertEqual(result["22 F1 20"]["display_name"], "Global Time")
        self.assertEqual(
            result["22 F1 22"]["display_name"],
            "Vehicle supply Voltage",
        )
        self.assertEqual(result["22 D1 00"]["display_name"], "Key Sw Number")

    def test_imports_rules_when_destination_is_empty(self):
        destination = self._temp_path()
        destination.write_text("{}", encoding="utf-8")

        result = import_display_name_rules(
            "22 F1 20 | Global Time",
            destination,
        )

        self.assertEqual(
            result,
            {"22 F1 20": {"display_name": "Global Time"}},
        )

    def test_accepts_existing_five_byte_display_name_key(self):
        destination = self._write_json(
            {"31 01 02 13 00": {"display_name": "Old Rule"}}
        )

        result = import_display_name_rules(
            "22 F1 20 | Global Time",
            destination,
        )

        self.assertIn("31 01 02 13 00", result)

    def test_rejects_invalid_rule_without_overwriting_destination(self):
        destination = self._write_json(
            {"22 F1 20": {"display_name": "Keep"}}
        )

        with self.assertRaises(ValueError):
            import_display_name_rules("22 F1 GG | Broken", destination)

        self.assertEqual(
            json.loads(destination.read_text(encoding="utf-8")),
            {"22 F1 20": {"display_name": "Keep"}},
        )
