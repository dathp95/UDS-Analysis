import json
import tempfile
import unittest
from pathlib import Path

from core.feature_access import (
    Feature,
    is_feature_enabled,
    load_deactivated_features,
)


class FeatureAccessTests(unittest.TestCase):

    def test_valid_license_enables_all_features(self):
        for feature in Feature:
            self.assertTrue(is_feature_enabled(feature, license_is_valid=True))

    def test_deactivated_feature_is_disabled_even_with_valid_license(self):
        self.assertFalse(
            is_feature_enabled(
                Feature.CAN_INTERFACE,
                license_is_valid=True,
                deactivated_features={Feature.CAN_INTERFACE},
            )
        )

    def test_invalid_license_only_enables_free_features(self):
        enabled = {
            feature
            for feature in Feature
            if is_feature_enabled(feature, license_is_valid=False)
        }

        self.assertEqual(
            enabled,
            {
                Feature.CRC_CONVERTER,
                Feature.LICENSE_SUPPORT,
            },
        )

    def test_load_deactivated_features_reads_release_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "release_features.json"
            config_file.write_text(
                json.dumps({"deactivated_features": ["can_interface"]}),
                encoding="utf-8",
            )

            self.assertEqual(
                load_deactivated_features(config_file),
                {Feature.CAN_INTERFACE},
            )


if __name__ == "__main__":
    unittest.main()
