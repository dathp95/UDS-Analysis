import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from gui.widgets.log_analyzer.filter_box import FilterBox


class FilterBoxRefreshTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_refresh_button_starts_disabled_and_emits_signal(self):
        widget = FilterBox()
        self.addCleanup(widget.deleteLater)
        emitted = []

        widget.refresh_clicked.connect(lambda: emitted.append(True))

        self.assertFalse(widget.btn_refresh.isEnabled())

        widget.fn_set_refresh_enabled(True)
        widget.btn_refresh.click()

        self.assertEqual(emitted, [True])


if __name__ == "__main__":
    unittest.main()
