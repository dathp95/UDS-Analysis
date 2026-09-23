import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QGroupBox,
    QLineEdit,
    QMessageBox,
    QSplitter,
)

from core.sleep_current_database import database_path_for_source, import_dataset
from gui.tabs.q_current_tab import PLACEHOLDER_VALUE, QCurrentTab
from gui.themes.theme import ThemeType
from gui.themes.theme_manager import ThemeManager
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_combobox import PrimaryComboBox


class QCurrentTabTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def tearDown(self):
        ThemeManager.fn_set_theme(ThemeType.LIGHT)

    def _create_tab(self, tmpdir: str):
        database_dir = Path(tmpdir) / "config" / "database_qcurrent"
        tab = QCurrentTab(database_dir=database_dir)
        self.addCleanup(tab.deleteLater)
        return tab, database_dir

    def test_analysis_settings_header_has_two_rows_and_file_controls(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_dir = self._create_tab(tmpdir)

            self.assertIsInstance(tab.settings_group, QGroupBox)
            self.assertEqual(tab.settings_group.title(), "Analysis Settings")
            self.assertEqual(tab.settings_layout.rowCount(), 2)
            self.assertIsInstance(tab.source_file_edit, QLineEdit)
            self.assertEqual(tab.source_file_edit.objectName(), "source_file_edit")
            self.assertTrue(tab.source_file_edit.isReadOnly())
            self.assertEqual(
                tab.source_file_edit.placeholderText(),
                "Select current data file (*.csv, *.xlsx)",
            )
            self.assertEqual(tab.browse_button.objectName(), "browse_button")
            self.assertEqual(tab.browse_button.text(), "Browse")
            self.assertIsInstance(tab.dataset_combo, PrimaryComboBox)
            self.assertEqual(tab.dataset_combo.objectName(), "dataset_combo")
            self.assertGreaterEqual(tab.dataset_combo.minimumWidth(), 220)
            self.assertEqual(tab.dataset_combo.count(), 0)
            self.assertEqual(tab.import_button.objectName(), "import_button")
            self.assertEqual(tab.import_button.text(), "Import")
            self.assertTrue(tab.import_button.isEnabled())
            self.assertEqual(tab.current_limit_label.text(), "Standard current (mA)")
            self.assertIsInstance(tab.current_limit_edit, QDoubleSpinBox)
            self.assertEqual(tab.current_limit_edit.minimum(), 0.0)
            self.assertEqual(tab.current_limit_edit.decimals(), 2)
            self.assertEqual(tab.current_limit_edit.value(), 30.0)
            self.assertEqual(tab.current_limit_edit.text(), "30.00")
            self.assertEqual(tab.analysis_result_edit.text(), "NOT RUN")

    def test_startup_keeps_dataset_combo_empty_until_user_opens_dropdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            database_dir = Path(tmpdir) / "database_qcurrent"
            database_file = database_dir / "sample.db"
            source_file = Path(tmpdir) / "sample.csv"
            source_file.write_text("Trigger time,No1 Average Ch1\n0,0.001\n", encoding="utf-8")
            import_dataset(
                "sample",
                source_file,
                [("0", 0.001, 1.0)],
                database_file,
            )

            tab = QCurrentTab(database_dir=database_dir)
            self.addCleanup(tab.deleteLater)

            self.assertEqual(tab.dataset_combo.count(), 0)

            tab.dataset_combo.showPopup()
            tab.dataset_combo.hidePopup()

            self.assertEqual(tab.dataset_combo.count(), 1)
            self.assertEqual(tab.dataset_combo.itemText(0), "sample")
            self.assertEqual(tab.dataset_combo.itemData(0), str(database_file.resolve()))

    def test_browse_cancel_keeps_existing_path_and_does_not_import(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_dir = self._create_tab(tmpdir)
            tab.source_file_edit.setText("C:/already/selected.csv")
            tab.source_file_edit.setToolTip("C:/already/selected.csv")

            with patch(
                "gui.tabs.q_current_tab.QFileDialog.getOpenFileName",
                return_value=("", ""),
            ), patch.object(tab, "import_current_file") as import_current_file:
                tab.browse_current_file()

            self.assertEqual(tab.source_file_edit.text(), "C:/already/selected.csv")
            self.assertEqual(tab.source_file_edit.toolTip(), "C:/already/selected.csv")
            self.assertEqual(tab.dataset_combo.count(), 0)
            import_current_file.assert_not_called()

    def test_browse_selects_absolute_file_path_enables_import_and_does_not_add_combo_item(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_dir = self._create_tab(tmpdir)
            source_file = Path(tmpdir) / "sample.csv"
            source_file.write_text("Trigger time,No1 Average Ch1\n0,0.001\n", encoding="utf-8")

            with patch(
                "gui.tabs.q_current_tab.QFileDialog.getOpenFileName",
                return_value=(str(source_file), "CSV Files (*.csv)"),
            ):
                tab.browse_current_file()

            self.assertEqual(tab.source_file_edit.text(), str(source_file.resolve()))
            self.assertEqual(tab.source_file_edit.toolTip(), str(source_file.resolve()))
            self.assertTrue(tab.import_button.isEnabled())
            self.assertEqual(tab.dataset_combo.count(), 0)

    def test_import_button_imports_selected_file_refreshes_combo_and_updates_header_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, database_dir = self._create_tab(tmpdir)
            existing_source = Path(tmpdir) / "VF6_Test.csv"
            existing_source.write_text("Trigger time,No1 Average Ch1\n0,0.001\n", encoding="utf-8")
            existing_database = database_path_for_source(existing_source, database_dir)
            import_dataset(
                "VF6_Test",
                existing_source,
                [("0", 0.001, 1.0)],
                existing_database,
            )
            tab._refresh_dataset_combo()
            self.assertEqual(tab.dataset_combo.currentText(), "VF6_Test")

            source_file = Path(tmpdir) / "sample.csv"
            source_file.write_text("Trigger time,No1 Average Ch7\n0,-1.2E-03\n", encoding="utf-8")
            tab.set_source_file(source_file)

            with patch("gui.tabs.q_current_tab.QMessageBox.information") as info_box:
                tab.import_current_file()

            self.assertEqual(tab.analysis_result_edit.text(), "IMPORTED")
            self.assertEqual(tab.current_import.row_count, 1)
            expected_database = database_path_for_source(source_file, database_dir)
            self.assertEqual(tab.current_database_path, expected_database)
            self.assertEqual(tab.dataset_combo.count(), 2)
            self.assertEqual(
                {tab.dataset_combo.itemText(index) for index in range(tab.dataset_combo.count())},
                {"VF6_Test", "sample"},
            )
            self.assertEqual(tab.dataset_combo.currentText(), "sample")
            self.assertEqual(tab.dataset_combo.currentData(), str(expected_database.resolve()))
            self.assertEqual(tab.source_file_edit.text(), "")
            self.assertEqual(tab.source_file_edit.toolTip(), "")
            self.assertTrue(tab.import_button.isEnabled())
            self.assertEqual(len(tab.current_samples), 1)
            self.assertTrue(expected_database.exists())
            info_box.assert_called_once()

    def test_import_button_loads_selected_dataset_into_data_review(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, database_dir = self._create_tab(tmpdir)
            source_file = Path(tmpdir) / "sample.csv"
            source_file.write_text("Trigger time,No1 Average Ch1\n0,0.001\n", encoding="utf-8")
            database_file = database_path_for_source(source_file, database_dir)
            import_dataset(
                "sample",
                source_file,
                [
                    ("26-09-11 11:41:29.036", -0.0169, -16.9),
                    ("26-09-11 11:41:30.079", -0.0173, -17.3),
                    ("26-09-11 11:41:31.101", -0.0158, -15.8),
                ],
                database_file,
            )
            tab._refresh_dataset_combo(selected_db_path=database_file)
            self.assertEqual(tab.source_file_edit.text(), "")

            with patch("gui.tabs.q_current_tab.QMessageBox.warning") as warning_box:
                tab.import_current_file()

            self.assertEqual(tab.current_database_path, database_file.resolve())
            self.assertEqual(len(tab.current_samples), 3)
            self.assertEqual(tab.review_table.rowCount(), 3)
            self.assertEqual(tab.review_table.columnCount(), 3)
            self.assertEqual(
                [tab.review_table.horizontalHeaderItem(index).text() for index in range(3)],
                ["No.", "Time", "Current (mA)"],
            )
            self.assertEqual(tab.review_table.item(0, 0).text(), "1")
            self.assertEqual(tab.review_table.item(0, 1).text(), "26-09-11 11:41:29.036")
            self.assertEqual(tab.review_table.item(0, 2).text(), "-16.90")
            self.assertEqual(tab.review_table.item(2, 0).text(), "3")
            self.assertEqual(tab.review_table.item(2, 2).text(), "-15.80")
            self.assertTrue(tab.import_button.isEnabled())
            warning_box.assert_not_called()

    def test_import_failure_keeps_source_combo_selection_and_import_enabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, database_dir = self._create_tab(tmpdir)
            existing_source = Path(tmpdir) / "VF6_Test.csv"
            existing_source.write_text("Trigger time,No1 Average Ch1\n0,0.001\n", encoding="utf-8")
            existing_database = database_path_for_source(existing_source, database_dir)
            import_dataset(
                "VF6_Test",
                existing_source,
                [("0", 0.001, 1.0)],
                existing_database,
            )
            tab._refresh_dataset_combo()
            selected_dataset = tab.dataset_combo.currentData()

            bad_source = Path(tmpdir) / "bad.txt"
            bad_source.write_text("not,current,data\n", encoding="utf-8")
            tab.set_source_file(bad_source)

            with patch("gui.tabs.q_current_tab.QMessageBox.warning") as warning_box:
                tab.import_current_file()

            self.assertEqual(tab.analysis_result_edit.text(), "IMPORT FAILED")
            self.assertEqual(tab.source_file_edit.text(), str(bad_source.resolve()))
            self.assertEqual(tab.source_file_edit.toolTip(), str(bad_source.resolve()))
            self.assertEqual(tab.dataset_combo.count(), 1)
            self.assertEqual(tab.dataset_combo.currentData(), selected_dataset)
            self.assertTrue(tab.import_button.isEnabled())
            warning_box.assert_called_once()

    def test_duplicate_import_no_cancel_keeps_existing_dataset_unchanged(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, database_dir = self._create_tab(tmpdir)
            source_file = Path(tmpdir) / "sample.csv"
            source_file.write_text("Trigger time,No1 Average Ch1\n0,0.001\n", encoding="utf-8")
            database_file = database_path_for_source(source_file, database_dir)
            first = import_dataset("sample", source_file, [("0", 0.001, 1.0)], database_file)
            tab._refresh_dataset_combo()
            source_file.write_text("Trigger time,No1 Average Ch1\n1,0.009\n", encoding="utf-8")
            tab.set_source_file(source_file)

            with patch(
                "gui.tabs.q_current_tab.QMessageBox.question",
                return_value=QMessageBox.No,
            ), patch("gui.tabs.q_current_tab.QMessageBox.information") as info_box:
                tab.import_current_file()

            tab._refresh_dataset_combo()
            self.assertEqual(tab.dataset_combo.count(), 1)
            self.assertEqual(tab.dataset_combo.itemData(0), str(database_file.resolve()))
            self.assertEqual(tab.analysis_result_edit.text(), "NOT RUN")
            info_box.assert_not_called()

    def test_duplicate_import_yes_replaces_dataset_and_selects_it(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, database_dir = self._create_tab(tmpdir)
            source_file = Path(tmpdir) / "sample.csv"
            source_file.write_text("Trigger time,No1 Average Ch1\n0,0.001\n", encoding="utf-8")
            database_file = database_path_for_source(source_file, database_dir)
            first = import_dataset("sample", source_file, [("0", 0.001, 1.0)], database_file)
            source_file.write_text("Trigger time,No1 Average Ch2\n1,0.009\n2,0.010\n", encoding="utf-8")
            tab.set_source_file(source_file)

            with patch(
                "gui.tabs.q_current_tab.QMessageBox.question",
                return_value=QMessageBox.Yes,
            ), patch("gui.tabs.q_current_tab.QMessageBox.information"):
                tab.import_current_file()

            self.assertEqual(tab.dataset_combo.count(), 1)
            self.assertEqual(tab.dataset_combo.currentData(), str(database_file.resolve()))
            self.assertEqual(tab.current_import.dataset.id, first.dataset.id)
            self.assertEqual(
                [(sample.time, sample.current_mA) for sample in tab.current_samples],
                [("1", 9.0), ("2", 10.0)],
            )

    def test_q_current_tab_keeps_non_settings_layout_regions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_dir = self._create_tab(tmpdir)

            self.assertIsInstance(tab.main_splitter, QSplitter)
            self.assertEqual(tab.main_splitter.orientation(), Qt.Horizontal)
            self.assertFalse(hasattr(tab, "information_group"))
            self.assertIs(tab.main_splitter.widget(0), tab.review_group)
            self.assertIs(tab.main_splitter.widget(1), tab.chart_group)
            self.assertIs(tab.main_splitter.widget(2), tab.right_panel)
            self.assertEqual(tab.chart_placeholder.text(), PLACEHOLDER_VALUE)
            self.assertEqual(tab.review_table.rowCount(), 0)
            self.assertEqual(tab.review_table.columnCount(), 3)
            self.assertEqual(tab.review_table.horizontalHeaderItem(0).text(), "No.")
            self.assertEqual(tab.review_table.horizontalHeaderItem(1).text(), "Time")
            self.assertEqual(tab.review_table.horizontalHeaderItem(2).text(), "Current (mA)")
            self.assertIn("sample_count", tab.summary_values)
            self.assertIn("duration", tab.summary_values)
            self.assertIn("min_current", tab.summary_values)
            self.assertIn("max_current", tab.summary_values)
            self.assertIn("avg_current", tab.summary_values)

    def test_q_current_tab_uses_existing_controls_and_theme_refresh(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_dir = self._create_tab(tmpdir)

            buttons = [
                tab.btn_run,
                tab.btn_export,
                tab.btn_copy_chart,
                tab.btn_clear,
            ]
            self.assertTrue(all(isinstance(button, PrimaryButton) for button in buttons))
            self.assertEqual([button.text() for button in buttons], [
                "RUN",
                "EXPORT",
                "COPY CHART",
                "CLEAR",
            ])

            light_style = tab.chart_placeholder.styleSheet()
            ThemeManager.fn_set_theme(ThemeType.DARK)
            tab.fn_refresh_theme()
            dark_style = tab.chart_placeholder.styleSheet()

            self.assertNotEqual(light_style, dark_style)
            self.assertIn(ThemeManager.fn_colors().TEXT, dark_style)


if __name__ == "__main__":
    unittest.main()
