import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent, QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox

from gui.themes.theme import ThemeType
from gui.themes.theme_manager import ThemeManager
from gui.widgets.log_analyzer.quick_access import QuickAccessWidget


class QuickAccessReorderWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2])
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "filters.json"
        self.filters = [
            {"id": i, "name": f"Filter {i}", "enabled": True,
             "filters": {"ecu": f"ECU{i}", "request": "22 F1 90", "response": "62 F1 90"},
             "extra": {"keep": i}}
            for i in range(1, 16)
        ]
        self.path.write_text(json.dumps(self.filters), encoding="utf-8")
        self.file_patch = patch("core.services.quick_access_service.QUICK_FILTER_FILE", self.path)
        self.file_patch.start()
        self.addCleanup(self.file_patch.stop)
        self.widget = QuickAccessWidget()
        self.addCleanup(self.widget.deleteLater)
        self.widget.resize(760, 460)
        self.widget.show()
        self.app.processEvents()

    def ids(self):
        return [button._quick_filter_data["id"] for button in self.widget.buttons]

    def drop(self, source_index, target_index):
        area = self.widget.scroll_area
        source = self.widget.buttons[source_index]
        target = self.widget.buttons[target_index]
        source_index = self.widget.buttons.index(source)
        target_index = self.widget.buttons.index(target)
        area.ensureWidgetVisible(target)
        self.app.processEvents()
        point = target.mapTo(area.viewport(), target.rect().topLeft())
        if target_index > source_index:
            point.setY(point.y() + target.height())
        mime = area.fn_mime_data(source)

        class Enter(QDragEnterEvent):
            def source(self):
                return source

        class Drop(QDropEvent):
            def source(self):
                return source

        enter = Enter(point, Qt.MoveAction, mime, Qt.LeftButton, Qt.NoModifier)
        area.dragEnterEvent(enter)
        self.assertTrue(enter.isAccepted())
        event = Drop(QPointF(point), Qt.MoveAction, mime, Qt.LeftButton, Qt.NoModifier)
        area.dropEvent(event)
        self.assertTrue(event.isAccepted())
        self.app.processEvents()

    def test_drag_first_last_and_last_first_preserves_selection_without_click_or_save(self):
        selected = self.widget.buttons[0]
        QTest.mouseClick(selected, Qt.LeftButton)
        signals = []
        self.widget.quick_filter_selected.connect(signals.append)
        original_bytes = self.path.read_bytes()
        self.drop(0, -1)
        self.assertEqual(self.ids(), list(range(2, 16)) + [1])
        self.assertIs(self.widget.buttons[-1], selected)
        self.assertEqual(self.widget.selected_filter["id"], 1)
        self.assertIn(ThemeManager.fn_colors().SUCCESS, selected.styleSheet())
        self.assertTrue(self.widget.btn_save_order.isEnabled())
        self.assertEqual(self.path.read_bytes(), original_bytes)
        self.assertEqual(signals, [])
        self.drop(-1, 0)
        self.assertEqual(self.ids(), list(range(1, 16)))
        self.assertFalse(self.widget.btn_save_order.isEnabled())

    def test_save_and_restart_and_search_save_complete_list(self):
        self.drop(0, -1)
        self.widget.edit_search.setText("ECU2")
        self.assertFalse(self.widget.scroll_area.reorder_enabled)
        self.assertTrue(self.widget.fn_save_order())
        self.assertFalse(self.widget.btn_save_order.isEnabled())
        restarted = QuickAccessWidget()
        self.addCleanup(restarted.deleteLater)
        self.assertEqual([f["id"] for f in restarted.quick_filters], list(range(2, 16)) + [1])
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), self.filters[1:] + self.filters[:1])

    def test_unsaved_order_does_not_survive_restart_or_search_changes(self):
        self.drop(0, -1)
        self.widget.edit_search.setText("ECU2")
        self.widget.edit_search.clear()
        self.assertEqual(self.ids(), list(range(2, 16)) + [1])
        self.assertTrue(self.widget.btn_save_order.isEnabled())
        restarted = QuickAccessWidget()
        self.addCleanup(restarted.deleteLater)
        self.assertEqual([f["id"] for f in restarted.quick_filters], list(range(1, 16)))

    def test_cancel_blocks_all_rebuilding_actions(self):
        self.drop(0, -1)
        current = self.widget.quick_filters[0]
        actions = [self.widget.fn_reload, self.widget.fn_add_filter, self.widget.fn_import_filters,
                   lambda: self.widget.fn_create_from_transaction({}),
                   lambda: self.widget._fn_edit_filter(current),
                   lambda: self.widget._fn_clone_filter(current),
                   lambda: self.widget._fn_delete_filter(current)]
        with patch("gui.widgets.log_analyzer.quick_access.QMessageBox.question", return_value=QMessageBox.Cancel) as question:
            for action in actions:
                action()
        self.assertEqual(question.call_count, len(actions))
        self.assertEqual(self.ids(), list(range(2, 16)) + [1])
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), self.filters)

    def test_reload_can_save_or_discard(self):
        for choice in (QMessageBox.Discard, QMessageBox.Save):
            with self.subTest(choice=choice):
                self.drop(0, -1)
                with patch("gui.widgets.log_analyzer.quick_access.QMessageBox.question", return_value=choice):
                    self.widget.fn_reload()
                expected = self.filters if choice == QMessageBox.Discard else self.filters[1:] + self.filters[:1]
                self.assertEqual(self.widget.quick_filters, expected)
                self.assertFalse(self.widget.btn_save_order.isEnabled())

    def test_save_failure_retains_unsaved_order_and_blocks_reload(self):
        self.drop(0, -1)
        with patch.object(self.widget.quick_access_controller, "fn_reorder", side_effect=ValueError("IDs changed")), patch(
            "gui.widgets.log_analyzer.quick_access.QMessageBox.warning"
        ) as warning, patch("gui.widgets.log_analyzer.quick_access.QMessageBox.question", return_value=QMessageBox.Save):
            self.widget.fn_reload()
        warning.assert_called_once()
        self.assertTrue(self.widget.btn_save_order.isEnabled())
        self.assertEqual(self.ids(), list(range(2, 16)) + [1])

    def test_click_context_menu_and_theme_still_work_after_reorder(self):
        self.drop(0, -1)
        calls = []
        self.widget.quick_filter_selected.connect(calls.append)
        QTest.mouseClick(self.widget.buttons[0], Qt.LeftButton)
        self.assertEqual(calls[0]["id"], 2)
        for action_name, handler in (("edit", "_fn_edit_filter"), ("clone", "_fn_clone_filter"), ("delete", "_fn_delete_filter")):
            with patch("gui.widgets.log_analyzer.quick_access.QMenu") as menu, patch.object(self.widget, handler) as action:
                menu.return_value.addAction.side_effect = ["edit", "clone", "delete"]
                menu.return_value.exec.return_value = action_name
                self.widget.buttons[0].customContextMenuRequested.emit(QPoint())
            action.assert_called_once_with(calls[0])
        original_theme = ThemeManager.fn_theme()
        try:
            for theme in (ThemeType.DARK, ThemeType.LIGHT):
                ThemeManager.fn_set_theme(theme)
                self.widget.fn_refresh_theme()
                self.assertIn(ThemeManager.fn_colors().SUCCESS, self.widget.buttons[0].styleSheet())
                self.assertTrue(self.widget.btn_save_order.isEnabled())
        finally:
            ThemeManager.fn_set_theme(original_theme)

    def test_mouse_drag_suppresses_click_and_next_normal_click_works(self):
        source = self.widget.buttons[0]
        calls = []
        self.widget.quick_filter_selected.connect(calls.append)
        from PySide6.QtCore import QEvent

        with patch("gui.widgets.log_analyzer.reorderable_filter_area.QDrag") as drag:
            drag.return_value.exec.side_effect = lambda *_: self.drop(0, -1)
            QTest.mousePress(source, Qt.LeftButton)
            position = QPointF(source.rect().center() + QPoint(0, 20))
            move = QMouseEvent(QEvent.MouseMove, position, position, Qt.NoButton, Qt.LeftButton, Qt.NoModifier)
            QApplication.sendEvent(source, move)
            QTest.mouseRelease(source, Qt.LeftButton)
            drag.return_value.exec.assert_called_once_with(Qt.MoveAction)
        self.assertEqual(calls, [])
        self.assertFalse(source.isDown())
        self.assertEqual(self.ids()[-1], 1)
        self.widget.scroll_area.ensureWidgetVisible(source)
        QTest.mouseClick(source, Qt.LeftButton)
        self.assertEqual([item["id"] for item in calls], [1])

    def test_drag_indicator_auto_scroll_and_cleanup(self):
        area = self.widget.scroll_area
        source = self.widget.buttons[0]
        mime = area.fn_mime_data(source)

        class Move(QDragMoveEvent):
            def source(self):
                return source

        point = QPoint(area.viewport().width() // 2, area.viewport().height() - 2)
        move = Move(point, Qt.MoveAction, mime, Qt.LeftButton, Qt.NoModifier)
        area.dragMoveEvent(move)
        self.assertTrue(move.isAccepted())
        self.assertTrue(area._indicator.isVisible())
        self.assertTrue(area._scroll_timer.isActive())
        before = area.verticalScrollBar().value()
        area._fn_auto_scroll()
        self.assertGreater(area.verticalScrollBar().value(), before)
        move = Move(QPoint(20, 1), Qt.MoveAction, mime, Qt.LeftButton, Qt.NoModifier)
        area.dragMoveEvent(move)
        area._fn_auto_scroll()
        self.assertLessEqual(area.verticalScrollBar().value(), before)
        area.dragLeaveEvent(QDragLeaveEvent())
        self.assertFalse(area._indicator.isVisible())
        self.assertFalse(area._scroll_timer.isActive())

    def test_search_and_disabled_buttons_reject_drops(self):
        area = self.widget.scroll_area
        source = self.widget.buttons[0]

        class Enter(QDragEnterEvent):
            def source(self):
                return source

        self.widget.edit_search.setText("ECU1")
        event = Enter(QPoint(20, 20), Qt.MoveAction, area.fn_mime_data(source), Qt.LeftButton, Qt.NoModifier)
        area.dragEnterEvent(event)
        self.assertFalse(event.isAccepted())
        self.widget.edit_search.clear()
        self.widget.fn_set_disabled()
        area.dragEnterEvent(event)
        self.assertFalse(event.isAccepted())
        self.widget.fn_reload()
        self.assertTrue(all(not button.isEnabled() for button in self.widget.buttons))

    def test_move_to_middle_and_clone_delete_use_existing_service(self):
        self.drop(0, 4)
        self.assertEqual(self.ids()[:5], [2, 3, 4, 5, 1])
        with patch("gui.widgets.log_analyzer.quick_access.QMessageBox.question", return_value=QMessageBox.Save):
            self.widget._fn_clone_filter(self.widget.quick_filters[0])
        self.assertEqual(len(self.widget.buttons), 16)
        cloned = self.widget.quick_filters[-1]
        self.assertEqual(cloned["name"], "Filter 2 (Copy)")
        self.assertEqual(cloned["filters"], self.filters[1]["filters"])
        self.widget._fn_delete_filter(cloned)
        self.assertEqual(self.ids(), [2, 3, 4, 5, 1] + list(range(6, 16)))


if __name__ == "__main__":
    unittest.main()
