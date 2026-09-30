import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from gui.widgets.log_analyzer.channel_selector import DiagnosticChannelSelectorWidget


class DiagnosticChannelSelectorWidgetTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_clear_shows_no_log_selected_disabled(self):
        widget = DiagnosticChannelSelectorWidget()
        self.addCleanup(widget.deleteLater)

        widget.fn_clear()

        self.assertFalse(widget.cmb_channel.isEnabled())
        self.assertEqual(widget.cmb_channel.currentText(), "No log selected")
        self.assertIsNone(widget.fn_channel())

    def test_single_channel_is_auto_selected_and_disabled(self):
        widget = DiagnosticChannelSelectorWidget()
        self.addCleanup(widget.deleteLater)

        widget.fn_set_channels([2])

        self.assertFalse(widget.cmb_channel.isEnabled())
        self.assertEqual(widget.cmb_channel.currentText(), "Channel 2")
        self.assertEqual(widget.fn_channel(), 2)

    def test_multiple_channels_require_user_selection(self):
        widget = DiagnosticChannelSelectorWidget()
        self.addCleanup(widget.deleteLater)

        widget.fn_set_channels([4, 1, 2])

        self.assertTrue(widget.cmb_channel.isEnabled())
        self.assertEqual(widget.cmb_channel.currentText(), "Select channel...")
        self.assertIsNone(widget.fn_channel())
        self.assertEqual(widget.cmb_channel.itemData(1), 1)
        self.assertEqual(widget.cmb_channel.itemText(1), "Channel 1")
        self.assertEqual(widget.cmb_channel.itemData(2), 2)
        self.assertEqual(widget.cmb_channel.itemData(3), 4)

        widget.cmb_channel.setCurrentIndex(2)

        self.assertEqual(widget.fn_channel(), 2)

    def test_no_channels_detected_is_disabled(self):
        widget = DiagnosticChannelSelectorWidget()
        self.addCleanup(widget.deleteLater)

        widget.fn_set_channels([])

        self.assertFalse(widget.cmb_channel.isEnabled())
        self.assertEqual(widget.cmb_channel.currentText(), "No CAN channel detected")
        self.assertIsNone(widget.fn_channel())


if __name__ == "__main__":
    unittest.main()
