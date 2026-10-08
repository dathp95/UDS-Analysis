import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QHBoxLayout

from gui.tabs.license_support_tab import LicenseSupportTab
from gui.widgets.controls.details_button import DetailsButton


class LicenseSupportDetailsTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_details_sections_start_collapsed(self):
        tab = LicenseSupportTab()
        self.addCleanup(tab.deleteLater)

        self.assertIsInstance(tab.layout(), QHBoxLayout)
        self.assertEqual(tab.layout().stretch(0), 30)
        self.assertEqual(tab.layout().stretch(1), 32)
        self.assertEqual(tab.layout().stretch(2), 38)

        for button in (
            tab.license_details_button,
            tab.activation_details_button,
            tab.guide_details_button,
        ):
            self.assertIsInstance(button, DetailsButton)
            self.assertFalse(button.is_expanded())
            self.assertEqual(button.text(), "< Details")

        self.assertTrue(tab.license_details_container.isHidden())
        self.assertTrue(tab.activation_details_container.isHidden())
        self.assertTrue(tab.guide_details_container.isHidden())

    def test_details_sections_toggle_independently(self):
        tab = LicenseSupportTab()
        self.addCleanup(tab.deleteLater)

        tab.license_details_button.click()

        self.assertFalse(tab.license_details_container.isHidden())
        self.assertTrue(tab.activation_details_container.isHidden())
        self.assertTrue(tab.guide_details_container.isHidden())
        self.assertEqual(tab.license_details_button.text(), "^ Details")
        self.assertEqual(tab.activation_details_button.text(), "> Details")

        tab.activation_details_button.click()

        self.assertFalse(tab.license_details_container.isHidden())
        self.assertFalse(tab.activation_details_container.isHidden())
        self.assertTrue(tab.guide_details_container.isHidden())

        tab.license_details_button.click()

        self.assertTrue(tab.license_details_container.isHidden())
        self.assertFalse(tab.activation_details_container.isHidden())
        self.assertTrue(tab.guide_details_container.isHidden())

    def test_existing_controls_remain_inside_details_containers(self):
        tab = LicenseSupportTab()
        self.addCleanup(tab.deleteLater)

        self.assertIs(tab.duration_combo.parentWidget(), tab.license_details_container)
        self.assertIs(tab.device_id_edit.parentWidget(), tab.activation_details_container)
        self.assertIs(tab.guide_browser.parentWidget(), tab.guide_details_container)
        self.assertEqual(
            tab.guide_browser.verticalScrollBarPolicy(),
            Qt.ScrollBarAsNeeded,
        )

        tab.license_details_button.click()
        tab.activation_details_button.click()
        tab.guide_details_button.click()

        tab.duration_combo.setCurrentText("6 Months")
        self.assertIn("720,000", tab.price_value_label.text())
        self.assertFalse(tab.qr_label.pixmap().isNull())
        tab.copy_device_id_button.click()
        self.assertEqual(QApplication.clipboard().text(), tab.device_id_edit.text())


if __name__ == "__main__":
    unittest.main()
