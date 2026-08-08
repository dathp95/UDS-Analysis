import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from gui.widgets.log_analyzer.filter_box import FilterBox


class FilterBoxPayloadEditingTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_typing_payload_byte_preserves_cursor_after_typed_character(self):
        widget = FilterBox()
        self.addCleanup(widget.deleteLater)
        edit = widget.edit_filter

        edit.show()
        edit.setFocus()
        edit.setText("22 F1 90")
        edit.setCursorPosition(4)

        QTest.keyClicks(edit, "3")
        self.application.processEvents()

        self.assertEqual(edit.text(), "22 F3 19 0")
        self.assertEqual(edit.cursorPosition(), 5)

    def test_delete_after_payload_character_removes_next_hex_character(self):
        widget = FilterBox()
        self.addCleanup(widget.deleteLater)
        edit = widget.edit_filter

        edit.show()
        edit.setFocus()
        edit.setText("22 F3 19 0")
        edit.setCursorPosition(5)

        QTest.keyClick(edit, Qt.Key_Delete)
        self.application.processEvents()

        self.assertEqual(edit.text(), "22 F3 90")
        self.assertEqual(edit.cursorPosition(), 5)


if __name__ == "__main__":
    unittest.main()
