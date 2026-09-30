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

    def test_multiple_channels_use_placeholder_without_selectable_item(self):
        widget = DiagnosticChannelSelectorWidget()
        self.addCleanup(widget.deleteLater)

        widget.fn_set_channels([4, 1, 2])

        self.assertTrue(widget.cmb_channel.isEnabled())
        self.assertEqual(widget.cmb_channel.placeholderText(), "Select channel...")
        self.assertEqual(widget.cmb_channel.currentIndex(), -1)
        self.assertIsNone(widget.fn_channel())
        self.assertEqual(widget.cmb_channel.count(), 3)
        self.assertEqual(
            [widget.cmb_channel.itemText(index) for index in range(widget.cmb_channel.count())],
            ["Channel 1", "Channel 2", "Channel 4"],
        )
        self.assertNotIn(
            "Select channel...",
            [widget.cmb_channel.itemText(index) for index in range(widget.cmb_channel.count())],
        )

    def test_channel_value_comes_from_item_data_not_index(self):
        widget = DiagnosticChannelSelectorWidget()
        self.addCleanup(widget.deleteLater)

        widget.fn_set_channels([2, 5, 12])
        widget.cmb_channel.setCurrentIndex(1)

        self.assertEqual(widget.cmb_channel.currentText(), "Channel 5")
        self.assertEqual(widget.cmb_channel.currentData(), 5)
        self.assertEqual(widget.fn_channel(), 5)

    def test_duplicate_channels_are_removed(self):
        widget = DiagnosticChannelSelectorWidget()
        self.addCleanup(widget.deleteLater)

        widget.fn_set_channels([1, 2, 2, 3, 1])

        self.assertEqual(widget.cmb_channel.count(), 3)
        self.assertEqual(
            [widget.cmb_channel.itemData(index) for index in range(widget.cmb_channel.count())],
            [1, 2, 3],
        )

    def test_no_channels_detected_is_disabled(self):
        widget = DiagnosticChannelSelectorWidget()
        self.addCleanup(widget.deleteLater)

        widget.fn_set_channels([])

        self.assertFalse(widget.cmb_channel.isEnabled())
        self.assertEqual(widget.cmb_channel.currentText(), "No CAN channel detected")
        self.assertIsNone(widget.fn_channel())


if __name__ == "__main__":
    unittest.main()
