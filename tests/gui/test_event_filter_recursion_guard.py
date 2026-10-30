import unittest
from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QApplication, QLineEdit, QPushButton

from gui.utils.text_selection import clear_text_selection_on_focus_out
from gui.widgets.log_analyzer.reorderable_filter_area import ReorderableFilterArea
from gui.widgets.log_analyzer.filter_box import FilterBox


class EventFilterRecursionGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_clear_text_selection_no_duplicate_filter(self):
        parent = QPushButton()
        edit = QLineEdit()
        # Call multiple times
        for _ in range(50):
            clear_text_selection_on_focus_out(parent, [edit])
        self.assertTrue(getattr(edit, "_has_focus_out_selection_clear", False))

    def test_reorderable_filter_area_unhandled_event_returns_false_without_recursion(self):
        area = ReorderableFilterArea()
        buttons = [QPushButton(f'Btn_{i}') for i in range(10)]
        area.fn_set_buttons(buttons)

        event = QEvent(QEvent.Type.StyleChange)
        # Dispatch event directly through filter
        for btn in buttons:
            handled = area.eventFilter(btn, event)
            self.assertFalse(handled)

    def test_filter_box_unhandled_event_returns_false(self):
        box = FilterBox()
        event = QEvent(QEvent.Type.StyleChange)
        handled = box.eventFilter(box.edit_filter, event)
        self.assertFalse(handled)

