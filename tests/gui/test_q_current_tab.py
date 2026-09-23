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

from core.sleep_current_database import import_dataset
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
        database_file = Path(tmpdir) / "config" / "database_qcurrent" / "sleep_current.db"
        tab = QCurrentTab(database_file=database_file)
        self.addCleanup(tab.deleteLater)
        return tab, database_file

    def test_analysis_settings_header_has_two_rows_and_file_controls(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_file = self._create_tab(tmpdir)

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
            self.assertFalse(tab.import_button.isEnabled())
            self.assertEqual(tab.current_limit_label.text(), "Standard current (mA)")
            self.assertIsInstance(tab.current_limit_edit, QDoubleSpinBox)
            self.assertEqual(tab.current_limit_edit.minimum(), 0.0)
            self.assertEqual(tab.current_limit_edit.decimals(), 2)
            self.assertEqual(tab.current_limit_edit.value(), 30.0)
            self.assertEqual(tab.current_limit_edit.text(), "30.00")
            self.assertEqual(tab.analysis_result_edit.text(), "NOT RUN")

    def test_startup_populates_dataset_combo_from_sqlite(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            database_file = Path(tmpdir) / "sleep_current.db"
            source_file = Path(tmpdir) / "sample.csv"
            source_file.write_text("Trigger time,No1 Average Ch1\n0,0.001\n", encoding="utf-8")
            result = import_dataset(
                "sample",
                source_file,
                [("0", 0.001, 1.0)],
                database_file,
            )

            tab = QCurrentTab(database_file=database_file)
            self.addCleanup(tab.deleteLater)

            self.assertEqual(tab.dataset_combo.count(), 1)
            self.assertEqual(tab.dataset_combo.itemText(0), "sample")
            self.assertEqual(tab.dataset_combo.itemData(0), result.dataset.id)

    def test_browse_cancel_keeps_existing_path_and_does_not_import(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_file = self._create_tab(tmpdir)
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
            tab, _database_file = self._create_tab(tmpdir)
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
            tab, database_file = self._create_tab(tmpdir)
            source_file = Path(tmpdir) / "sample.csv"
            source_file.write_text("Trigger time,No1 Average Ch7\n0,-1.2E-03\n", encoding="utf-8")
            tab.set_source_file(source_file)

            with patch("gui.tabs.q_current_tab.QMessageBox.information") as info_box:
                tab.import_current_file()

            self.assertEqual(tab.analysis_result_edit.text(), "IMPORTED")
            self.assertEqual(tab.current_import.row_count, 1)
            self.assertEqual(tab.current_database_path, database_file.resolve())
            self.assertEqual(tab.dataset_combo.count(), 1)
            self.assertEqual(tab.dataset_combo.currentText(), "sample")
            self.assertEqual(len(tab.current_samples), 1)
            self.assertTrue(database_file.exists())
            info_box.assert_called_once()

    def test_duplicate_import_no_cancel_keeps_existing_dataset_unchanged(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, database_file = self._create_tab(tmpdir)
            source_file = Path(tmpdir) / "sample.csv"
            source_file.write_text("Trigger time,No1 Average Ch1\n0,0.001\n", encoding="utf-8")
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
            self.assertEqual(tab.dataset_combo.itemData(0), first.dataset.id)
            self.assertEqual(tab.analysis_result_edit.text(), "NOT RUN")
            info_box.assert_not_called()

    def test_duplicate_import_yes_replaces_dataset_and_selects_it(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, database_file = self._create_tab(tmpdir)
            source_file = Path(tmpdir) / "sample.csv"
            source_file.write_text("Trigger time,No1 Average Ch1\n0,0.001\n", encoding="utf-8")
            first = import_dataset("sample", source_file, [("0", 0.001, 1.0)], database_file)
            source_file.write_text("Trigger time,No1 Average Ch2\n1,0.009\n2,0.010\n", encoding="utf-8")
            tab.set_source_file(source_file)

            with patch(
                "gui.tabs.q_current_tab.QMessageBox.question",
                return_value=QMessageBox.Yes,
            ), patch("gui.tabs.q_current_tab.QMessageBox.information"):
                tab.import_current_file()

            self.assertEqual(tab.dataset_combo.count(), 1)
            self.assertEqual(tab.dataset_combo.currentData(), first.dataset.id)
            self.assertEqual(tab.current_import.dataset.id, first.dataset.id)
            self.assertEqual(
                [(sample.time, sample.current_mA) for sample in tab.current_samples],
                [("1", 9.0), ("2", 10.0)],
            )

    def test_q_current_tab_keeps_non_settings_layout_regions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_file = self._create_tab(tmpdir)

            self.assertIsInstance(tab.main_splitter, QSplitter)
            self.assertEqual(tab.main_splitter.orientation(), Qt.Horizontal)
            self.assertIs(tab.main_splitter.widget(0), tab.information_group)
            self.assertIs(tab.main_splitter.widget(1), tab.center_splitter)
            self.assertIs(tab.main_splitter.widget(2), tab.right_panel)
            self.assertEqual(tab.center_splitter.orientation(), Qt.Vertical)
            self.assertIs(tab.center_splitter.widget(0), tab.chart_group)
            self.assertIs(tab.center_splitter.widget(1), tab.review_group)
            self.assertEqual(tab.chart_placeholder.text(), PLACEHOLDER_VALUE)
            self.assertEqual(tab.review_placeholder.text(), PLACEHOLDER_VALUE)

    def test_q_current_tab_uses_existing_controls_and_theme_refresh(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_file = self._create_tab(tmpdir)

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
