import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from gui.dialogs.export_quick_filters_dialog import ExportQuickFiltersDialog
from gui.widgets.log_analyzer.left_panel import LeftPanel
from gui.widgets.log_analyzer.quick_access import QuickAccessWidget


class QuickAccessExportWidgetTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_quick_access_has_bottom_action_buttons(self):
        widget = QuickAccessWidget()
        self.addCleanup(widget.deleteLater)

        layout = widget.layout()

        self.assertIs(layout.itemAt(0).widget(), widget.scroll_area)
        self.assertEqual(layout.stretch(0), 1)
        self.assertIs(layout.itemAt(1).layout(), widget.action_layout)
        self.assertEqual(widget.action_layout.indexOf(widget.btn_add), 0)
        self.assertEqual(widget.action_layout.indexOf(widget.btn_import), 1)
        self.assertEqual(widget.action_layout.indexOf(widget.btn_export), 2)
        self.assertEqual(widget.btn_add.text(), "+ Add Filter +")
        self.assertEqual(widget.btn_import.text(), "Import Filters")
        self.assertEqual(widget.btn_export.text(), "Export Filters")


    def test_left_panel_gives_remaining_area_to_quick_filter(self):
        panel = LeftPanel()
        self.addCleanup(panel.deleteLater)

        layout = panel.layout()

        self.assertEqual(layout.count(), 1)
        self.assertIs(layout.itemAt(0).widget(), panel.quick_access)
        self.assertEqual(layout.stretch(0), 1)

    def test_quick_access_opens_export_dialog_with_exported_filters(self):
        widget = QuickAccessWidget()
        self.addCleanup(widget.deleteLater)

        with patch.object(
            widget.quick_access_controller,
            "fn_export_filters",
            return_value="Read VIN MHU|MHU|22 F1 90|62 F1 90",
        ) as export_filters, patch(
            "gui.widgets.log_analyzer.quick_access.ExportQuickFiltersDialog"
        ) as dialog:
            widget.fn_export_filters()

        export_filters.assert_called_once_with()
        dialog.assert_called_once_with(
            "Read VIN MHU|MHU|22 F1 90|62 F1 90",
            widget,
        )
        dialog.return_value.exec.assert_called_once_with()

    def test_export_quick_filters_dialog_uses_import_filter_format(self):
        dialog = ExportQuickFiltersDialog(
            "Read VIN MHU|MHU|22 F1 90|62 F1 90"
        )
        self.addCleanup(dialog.deleteLater)

        self.assertEqual(
            dialog.fn_export_text(),
            "Read VIN MHU|MHU|22 F1 90|62 F1 90",
        )
        self.assertTrue(dialog.txt_filters.isReadOnly())


if __name__ == "__main__":
    unittest.main()
