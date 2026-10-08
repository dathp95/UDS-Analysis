import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from gui.widgets.controls.details_button import DetailsButton


class DetailsButtonTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_details_button_toggles_state_text_and_signal(self):
        button = DetailsButton()
        self.addCleanup(button.deleteLater)
        emitted = []
        button.expandedChanged.connect(emitted.append)

        self.assertFalse(button.is_expanded())
        self.assertEqual(button.text(), "> Details")
        self.assertEqual(button.cursor().shape(), Qt.PointingHandCursor)

        button.click()

        self.assertTrue(button.is_expanded())
        self.assertEqual(button.text(), "^ Details")
        self.assertEqual(emitted, [True])

        button.click()

        self.assertFalse(button.is_expanded())
        self.assertEqual(button.text(), "> Details")
        self.assertEqual(emitted, [True, False])

    def test_set_expanded_is_idempotent(self):
        button = DetailsButton()
        self.addCleanup(button.deleteLater)
        emitted = []
        button.expandedChanged.connect(emitted.append)

        button.set_expanded(True)
        button.set_expanded(True)
        button.set_expanded(False)
        button.set_expanded(False)

        self.assertEqual(emitted, [True, False])
        self.assertEqual(button.text(), "> Details")


if __name__ == "__main__":
    unittest.main()
