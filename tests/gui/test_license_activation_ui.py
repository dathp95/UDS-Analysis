import os
import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from gui.tabs.license_support_tab import LicenseSupportTab
from license.activation import ActivationResult
from license.manager import LicenseStatus
from license.models import License


class LicenseActivationUITests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_device_id_field_uses_license_manager_device_id(self):
        with patch(
            "gui.tabs.license_support_tab.LicenseManager.get_device_id",
            return_value="VC-AAAA-BBBB-CCCC-DDDD-EEEE",
        ), patch(
            "gui.tabs.license_support_tab.LicenseManager.get_status",
            return_value=LicenseStatus.invalid("missing activation"),
        ):
            tab = LicenseSupportTab()
            self.addCleanup(tab.deleteLater)

        self.assertEqual(
            tab.device_id_edit.text(),
            "VC-AAAA-BBBB-CCCC-DDDD-EEEE",
        )
        self.assertTrue(tab.device_id_edit.isReadOnly())

    def test_activate_button_updates_status_from_activation_result(self):
        expire_date = datetime.now(UTC) + timedelta(days=30)
        license_model = License(
            customer="Test Customer",
            edition="Professional",
            issue_date=datetime.now(UTC),
            expire_date=expire_date,
        )
        with patch(
            "gui.tabs.license_support_tab.LicenseManager.get_device_id",
            return_value="VC-AAAA-BBBB-CCCC-DDDD-EEEE",
        ), patch(
            "gui.tabs.license_support_tab.LicenseManager.get_status",
            return_value=LicenseStatus.invalid("missing activation"),
        ), patch(
            "gui.tabs.license_support_tab.LicenseManager.activate",
            return_value=ActivationResult.ok(license_model),
        ) as activate:
            tab = LicenseSupportTab()
            self.addCleanup(tab.deleteLater)
            tab.activation_key_edit.setPlainText("activation-token")

            tab.activate_button.click()

        activate.assert_called_once_with("activation-token")
        self.assertEqual(tab.status_value_label.text(), "Activated")
        self.assertEqual(tab.edition_value_label.text(), "Professional")
        self.assertIn(expire_date.strftime("%d/%m/%Y"), tab.expire_date_value_label.text())
        self.assertIn("day(s)", tab.remaining_value_label.text())

    def test_failed_activation_does_not_grant_activated_status(self):
        with patch(
            "gui.tabs.license_support_tab.LicenseManager.get_device_id",
            return_value="VC-AAAA-BBBB-CCCC-DDDD-EEEE",
        ), patch(
            "gui.tabs.license_support_tab.LicenseManager.get_status",
            return_value=LicenseStatus.invalid("missing activation"),
        ), patch(
            "gui.tabs.license_support_tab.LicenseManager.activate",
            return_value=ActivationResult.failed("bad activation"),
        ):
            tab = LicenseSupportTab()
            self.addCleanup(tab.deleteLater)

            tab.activate_button.click()

        self.assertEqual(tab.status_value_label.text(), "Activation Failed")
        self.assertEqual(tab.edition_value_label.text(), "--")
        self.assertEqual(tab.status_value_label.toolTip(), "bad activation")


if __name__ == "__main__":
    unittest.main()
