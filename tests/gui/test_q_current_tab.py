import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QGroupBox, QLineEdit, QSplitter

from gui.tabs.q_current_tab import PLACEHOLDER_VALUE, QCurrentTab
from gui.themes.theme import ThemeType
from gui.themes.theme_manager import ThemeManager
from gui.widgets.controls.primary_button import PrimaryButton


class QCurrentTabTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def tearDown(self):
        ThemeManager.fn_set_theme(ThemeType.LIGHT)

    def test_analysis_settings_header_has_two_rows_and_file_controls(self):
        tab = QCurrentTab()
        self.addCleanup(tab.deleteLater)

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
        self.assertEqual(tab.import_button.objectName(), "import_button")
        self.assertEqual(tab.import_button.text(), "Import")
        self.assertFalse(tab.import_button.isEnabled())
        self.assertEqual(tab.current_limit_edit.text(), "30.00 mA")
        self.assertEqual(tab.analysis_result_edit.text(), "NOT RUN")

    def test_browse_cancel_keeps_existing_path_and_does_not_import(self):
        tab = QCurrentTab()
        self.addCleanup(tab.deleteLater)
        tab.source_file_edit.setText("C:/already/selected.csv")
        tab.source_file_edit.setToolTip("C:/already/selected.csv")

        with patch(
            "gui.tabs.q_current_tab.QFileDialog.getOpenFileName",
            return_value=("", ""),
        ), patch.object(tab, "import_current_file") as import_current_file:
            tab.browse_current_file()

        self.assertEqual(tab.source_file_edit.text(), "C:/already/selected.csv")
        self.assertEqual(tab.source_file_edit.toolTip(), "C:/already/selected.csv")
        import_current_file.assert_not_called()

    def test_browse_selects_absolute_file_path_and_enables_import(self):
        tab = QCurrentTab()
        self.addCleanup(tab.deleteLater)

        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "sample.csv"
            source_file.write_text("time,current_ma\n0,1\n", encoding="utf-8")

            with patch(
                "gui.tabs.q_current_tab.QFileDialog.getOpenFileName",
                return_value=(str(source_file), "CSV Files (*.csv)"),
            ):
                tab.browse_current_file()

            self.assertEqual(tab.source_file_edit.text(), str(source_file.resolve()))
            self.assertEqual(tab.source_file_edit.toolTip(), str(source_file.resolve()))
            self.assertTrue(tab.import_button.isEnabled())

    def test_import_button_imports_selected_file_and_updates_header_state(self):
        tab = QCurrentTab()
        self.addCleanup(tab.deleteLater)

        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "sample.csv"
            source_file.write_text("time,current_ma\n0,1.2\n", encoding="utf-8")
            tab.set_source_file(source_file)

            with patch(
                "core.q_current_import.QCURRENT_REPORT_DIR",
                Path(tmpdir) / "Report Qcurrent",
            ), patch(
                "gui.tabs.q_current_tab.QMessageBox.information"
            ) as info_box:
                tab.import_current_file()

            self.assertEqual(tab.analysis_result_edit.text(), "IMPORTED")
            self.assertEqual(tab.current_import.row_count, 1)
            self.assertTrue(tab.current_database_path.exists())
            info_box.assert_called_once()

    def test_q_current_tab_keeps_non_settings_layout_regions(self):
        tab = QCurrentTab()
        self.addCleanup(tab.deleteLater)

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
        tab = QCurrentTab()
        self.addCleanup(tab.deleteLater)

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