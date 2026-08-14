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
