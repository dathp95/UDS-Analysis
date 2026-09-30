import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from gui.dialogs.export_quick_filters_dialog import ExportQuickFiltersDialog
from gui.dialogs.quick_filter_dialog import QuickFilterDialog
from gui.widgets.controls.primary_lineedit import PrimaryLineEdit
from gui.widgets.log_analyzer.left_panel import LeftPanel
from gui.widgets.log_analyzer.quick_access import QuickAccessWidget


class QuickAccessExportWidgetTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_quick_access_has_search_and_bottom_action_buttons(self):
        widget = QuickAccessWidget()
        self.addCleanup(widget.deleteLater)

        layout = widget.layout()

        self.assertIsInstance(widget.edit_search, PrimaryLineEdit)
        self.assertEqual(widget.edit_search.placeholderText(), "Search Quick Filter...")
        self.assertIs(layout.itemAt(0).widget(), widget.scroll_area)
        self.assertEqual(layout.stretch(0), 1)
        self.assertIs(layout.itemAt(1).layout(), widget.action_layout)
        self.assertEqual(widget.action_layout.indexOf(widget.btn_add), 0)
        self.assertEqual(widget.action_layout.indexOf(widget.btn_import), 1)
        self.assertEqual(widget.action_layout.indexOf(widget.btn_export), 2)
        self.assertEqual(widget.btn_add.text(), "+ Add Filter +")
        self.assertEqual(widget.btn_import.text(), "Import Filters")
        self.assertEqual(widget.btn_export.text(), "Export Filters")

    def test_quick_filter_search_matches_name_ecu_request_and_response(self):
        widget = QuickAccessWidget()
        self.addCleanup(widget.deleteLater)

        widget.quick_filters = [
            {
                "name": "Read VIN",
                "filters": {
                    "ecu": "VCU",
                    "request": "22 F1 90",
                    "response": "62 F1 90",
                },
            },
            {
                "name": "Read DTC",
                "filters": {
                    "ecu": "ECU",
                    "request": "19 02",
                    "response": "59 02",
                },
            },
            {
                "name": "Clear DTC",
                "filters": {
                    "ecu": "ECU",
                    "request": "14 FF FF FF",
                    "response": "54",
                },
            },
        ]
        widget._fn_clear_buttons()
        widget._fn_build_buttons()

        widget.edit_search.setText(" dtc ")
        self.assertEqual(
            [button.text() for button in widget.buttons if not button.isHidden()],
            ["Read DTC", "Clear DTC"],
        )

        widget.edit_search.setText("VCU")
        self.assertEqual(
            [button.text() for button in widget.buttons if not button.isHidden()],
            ["Read VIN"],
        )

        widget.edit_search.setText("22   F1 90")
        self.assertEqual(
            [button.text() for button in widget.buttons if not button.isHidden()],
            ["Read VIN"],
        )

        widget.edit_search.setText("62 F1 90")
        self.assertEqual(
            [button.text() for button in widget.buttons if not button.isHidden()],
            ["Read VIN"],
        )

        widget.edit_search.clear()
        self.assertEqual(
            [button.text() for button in widget.buttons if not button.isHidden()],
            ["Read VIN", "Read DTC", "Clear DTC"],
        )

    def test_quick_filter_search_reapplies_after_reload_without_enabling_buttons(self):
        widget = QuickAccessWidget()
        self.addCleanup(widget.deleteLater)

        filters = [
            {"name": "Read VIN", "filters": {"ecu": "VCU"}},
            {"name": "Read DTC", "filters": {"ecu": "ECU"}},
        ]

        with patch.object(widget.quick_access_controller, "fn_load", return_value=filters):
            widget.edit_search.setText("VIN")
            widget.fn_reload()

        self.assertEqual(widget.edit_search.text(), "VIN")
        self.assertEqual(
            [button.text() for button in widget.buttons if not button.isHidden()],
            ["Read VIN"],
        )

        widget.fn_set_disabled()
        widget.edit_search.setText("DTC")

        self.assertEqual(
            [button.text() for button in widget.buttons if not button.isHidden()],
            ["Read DTC"],
        )
        self.assertFalse(widget.buttons[1].isEnabled())

    def test_create_from_transaction_prefills_dialog_and_saves_edited_filter(self):
        widget = QuickAccessWidget()
        self.addCleanup(widget.deleteLater)

        row_data = {
            "ECU": "MHU",
            "Request": "22 F1 90",
            "Response": "62 F1 90 56 49 4E",
            "Time": "42.500",
            "Status": "Positive",
        }
        saved_filter = {
            "name": "Read VIN MHU",
            "filters": {
                "ecu": "MHU",
                "request": "22 F1 90",
                "response": "62 F1 90",
            },
        }

        with patch(
            "gui.widgets.log_analyzer.quick_access.QuickFilterDialog"
        ) as dialog_class, patch.object(
            widget.quick_access_controller,
            "fn_add",
        ) as add_filter, patch.object(widget, "fn_reload") as reload_filters:
            dialog = dialog_class.return_value
            dialog.exec.return_value = True
            dialog.fn_get_data.return_value = saved_filter

            widget.fn_create_from_transaction(row_data)

        dialog_class.assert_called_once_with(
            quick_filter={
                "name": "",
                "filters": {
                    "ecu": "MHU",
                    "request": "22 F1 90",
                    "response": "62 F1 90 56 49 4E",
                },
            },
            parent=widget,
        )
        add_filter.assert_called_once_with(saved_filter)
        reload_filters.assert_called_once_with()

    def test_create_from_transaction_cancel_does_not_save(self):
        widget = QuickAccessWidget()
        self.addCleanup(widget.deleteLater)

        with patch(
            "gui.widgets.log_analyzer.quick_access.QuickFilterDialog"
        ) as dialog_class, patch.object(
            widget.quick_access_controller,
            "fn_add",
        ) as add_filter, patch.object(widget, "fn_reload") as reload_filters:
            dialog_class.return_value.exec.return_value = False

            widget.fn_create_from_transaction(
                {
                    "ECU": "MHU",
                    "Request": "22 F1 90",
                    "Response": "62 F1 90",
                }
            )

        add_filter.assert_not_called()
        reload_filters.assert_not_called()

    def test_quick_filter_dialog_accepts_add_draft_without_id_or_enabled(self):
        dialog = QuickFilterDialog(
            quick_filter={
                "name": "",
                "filters": {
                    "ecu": "MHU",
                    "request": "22 F1 90",
                    "response": "62 F1 90 56 49 4E",
                },
            }
        )
        self.addCleanup(dialog.deleteLater)

        dialog.fields["name"].setText("Read VIN MHU")
        dialog.fields["response"].setText("62 F1 90")

        self.assertEqual(
            dialog.fn_get_data(),
            {
                "name": "Read VIN MHU",
                "filters": {
                    "ecu": "MHU",
                    "request": "22 F1 90",
                    "response": "62 F1 90",
                },
            },
        )
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



