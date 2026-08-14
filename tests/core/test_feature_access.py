import unittest

from core.feature_access import Feature, is_feature_enabled


class FeatureAccessTests(unittest.TestCase):

    def test_valid_license_enables_all_features(self):
        for feature in Feature:
            self.assertTrue(is_feature_enabled(feature, license_is_valid=True))

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


if __name__ == "__main__":
    unittest.main()
