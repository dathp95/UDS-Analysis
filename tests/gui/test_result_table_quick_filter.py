import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QHeaderView

from gui.widgets.log_analyzer.result_table import ResultTable


class ResultTableQuickFilterTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])


    def test_status_column_stretches_to_fill_remaining_width(self):
        table = ResultTable()
        self.addCleanup(table.deleteLater)

        status_column = table._fn_column_index("Status")
        request_column = table._fn_column_index("Request")

        self.assertEqual(
            table.horizontalHeader().sectionResizeMode(status_column),
            QHeaderView.Stretch,
        )
        self.assertEqual(
            table.horizontalHeader().sectionResizeMode(request_column),
            QHeaderView.Interactive,
        )

    def test_header_sorting_is_disabled_without_changing_resize_mode(self):
        table = ResultTable()
        self.addCleanup(table.deleteLater)

        table.set_data([
            {
                "ECU": "ZCU",
                "Time": "2.000",
                "Activity": "Second",
                "Request": "22 F1 91",
                "Response": "62 F1 91",
                "RT (ms)": "20",
                "Status": "OK",
            },
            {
                "ECU": "ACU",
                "Time": "1.000",
                "Activity": "First",
                "Request": "22 F1 90",
                "Response": "62 F1 90",
                "RT (ms)": "10",
                "Status": "OK",
            },
        ])

        header = table.horizontalHeader()
        ecu_column = table._fn_column_index("ECU")
        before = [table.item(row, ecu_column).text() for row in range(table.rowCount())]

        header.sectionClicked.emit(ecu_column)
        after = [table.item(row, ecu_column).text() for row in range(table.rowCount())]

        self.assertFalse(table.isSortingEnabled())
        self.assertFalse(header.isSortIndicatorShown())
        self.assertEqual(after, before)
        self.assertEqual(
            header.sectionResizeMode(ecu_column),
            QHeaderView.Interactive,
        )

    def test_row_data_returns_displayed_selected_row_values(self):
        table = ResultTable()
        self.addCleanup(table.deleteLater)

        row_data = {
            "ECU": "VCU",
            "Time": "125.320",
            "Activity": "Read VIN",
            "Request": "22 F1 90",
            "Response": "62 F1 90",
            "RT (ms)": "15.20",
            "Status": "Positive",
        }
        table.set_data([row_data])

        self.assertEqual(table.fn_row_data(0), row_data)
        self.assertEqual(table.fn_row_data(-1), {})
    def test_apply_quick_filter_clears_previous_row_selection(self):
        table = ResultTable()
        self.addCleanup(table.deleteLater)

        table.set_data([
            {
                "ECU": "ECU1",
                "Time": "0.001",
                "Activity": "Diag",
                "Request": "22 F1 90",
                "Response": "62 F1 90",
                "RT (ms)": "10",
                "Status": "OK",
            },
            {
                "ECU": "ECU2",
                "Time": "0.002",
                "Activity": "Diag",
                "Request": "22 F1 91",
                "Response": "62 F1 91",
                "RT (ms)": "11",
                "Status": "OK",
            },
        ])

        filter_2 = {
            "filters": {
                "ecu": "ECU2",
                "request": "",
                "response": "",
            }
        }
        filter_1 = {
            "filters": {
                "ecu": "ECU1",
                "request": "",
                "response": "",
            }
        }

        table.fn_apply_quick_filter(filter_2)
        table.selectRow(1)
        self.assertEqual(table.currentRow(), 1)
        self.assertTrue(table.selectionModel().selectedRows())

        table.fn_apply_quick_filter(filter_1)
        self.assertEqual(table.currentRow(), -1)
        self.assertFalse(table.selectionModel().selectedRows())

        table.fn_apply_quick_filter(filter_2)
        self.assertEqual(table.currentRow(), -1)
        self.assertFalse(table.selectionModel().selectedRows())


if __name__ == "__main__":
    unittest.main()

