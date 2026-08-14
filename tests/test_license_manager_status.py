import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from license.exceptions import LicenseError
from license.manager import LicenseManager
from license.models import License


class LicenseManagerStatusTests(unittest.TestCase):

    def test_get_status_returns_valid_status_with_license(self):
        license_model = License(
            customer="Test Customer",
            edition="Pro",
            issue_date=datetime.now(),
            expire_date=datetime.now() + timedelta(days=30),
        )

        with patch.object(LicenseManager, "validate", return_value=license_model):
            status = LicenseManager.get_status()

        self.assertTrue(status.is_valid)
        self.assertIs(status.license, license_model)
        self.assertEqual(status.error_message, "")

    def test_get_status_returns_invalid_status_without_raising(self):
        with patch.object(LicenseManager, "validate", side_effect=LicenseError("bad license")):
            status = LicenseManager.get_status()

        self.assertFalse(status.is_valid)
        self.assertIsNone(status.license)
        self.assertEqual(status.error_message, "bad license")


if __name__ == "__main__":
    unittest.main()
