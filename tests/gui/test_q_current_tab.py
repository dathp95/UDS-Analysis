import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QFocusEvent
from PySide6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QGroupBox,
    QLineEdit,
    QMessageBox,
    QSplitter,
)

from core.sleep_current_database import database_path_for_source, import_dataset
from gui.tabs.q_current_tab import (
    PLACEHOLDER_VALUE,
    QCurrentTab,
    calculate_elapsed_seconds,
    detect_wake_up_intervals,
)
from gui.themes.theme import ThemeType
from gui.themes.theme_manager import ThemeManager
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_combobox import PrimaryComboBox
from gui.widgets.controls.quick_access_button import QuickAccessButton


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


    def _legend_labels(self, tab):
        return [item.legend_text for item in tab.legend_items]

    def _sample(self, time, current_ma):
        return type("Sample", (), {"time": str(time), "current_mA": current_ma})()

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
            self.assertEqual(tab.current_limit_label.text(), "Sleep limit (mA)")
            self.assertIsInstance(tab.current_limit_edit, QDoubleSpinBox)
            self.assertEqual(tab.current_limit_edit.objectName(), "current_limit_edit")
            self.assertEqual(tab.current_limit_edit.minimum(), 0.0)
            self.assertEqual(tab.current_limit_edit.decimals(), 1)
            self.assertEqual(tab.current_limit_edit.value(), 30.0)
            self.assertEqual(tab.current_limit_edit.text(), "30.0")
            self.assertEqual(tab.wake_limit_label.text(), "Wake Up limit (mA)")
            self.assertIsInstance(tab.wake_limit_edit, QDoubleSpinBox)
            self.assertEqual(tab.wake_limit_edit.objectName(), "wake_limit_edit")
            self.assertEqual(tab.wake_limit_edit.minimum(), 0.0)
            self.assertEqual(tab.sleep_duration_label.text(), "Sleep duration (s)")
            self.assertIsInstance(tab.sleep_duration_edit, QDoubleSpinBox)
            self.assertEqual(tab.sleep_duration_edit.objectName(), "sleep_duration_edit")
            self.assertEqual(tab.sleep_duration_edit.minimum(), 10.0)
            self.assertEqual(tab.sleep_duration_edit.decimals(), 1)
            self.assertEqual(tab.sleep_duration_edit.value(), 60.0)
            self.assertEqual(tab.sleep_duration_edit.text(), "60.0")
            self.assertEqual(tab.wake_limit_edit.decimals(), 1)
            self.assertEqual(tab.wake_limit_edit.value(), 300.0)
            self.assertEqual(tab.wake_limit_edit.text(), "300.0")
            self.assertEqual(tab.wake_duration_label.text(), "Wake duration (s)")
            self.assertIsInstance(tab.wake_duration_edit, QDoubleSpinBox)
            self.assertEqual(tab.wake_duration_edit.objectName(), "wake_duration_edit")
            self.assertEqual(tab.wake_duration_edit.minimum(), 1.0)
            self.assertEqual(tab.wake_duration_edit.maximum(), 3600.0)
            self.assertEqual(tab.wake_duration_edit.singleStep(), 0.5)
            self.assertEqual(tab.wake_duration_edit.decimals(), 1)
            self.assertEqual(tab.wake_duration_edit.value(), 2.0)
            self.assertEqual(tab.wake_duration_edit.text(), "2.0")
            self.assertEqual(tab.analysis_result_edit.text(), "NOT RUN")


    def test_q_current_action_buttons_start_disabled_until_data_loads(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_dir = self._create_tab(tmpdir)

            self.assertTrue(tab.browse_button.isEnabled())
            self.assertTrue(tab.import_button.isEnabled())
            self.assertFalse(tab.btn_run.isEnabled())
            self.assertFalse(tab.btn_copy_data_review.isEnabled())
            self.assertFalse(tab.btn_export.isEnabled())
            self.assertFalse(tab.btn_copy_chart.isEnabled())
            self.assertFalse(tab.btn_capture_chart.isEnabled())
            self.assertFalse(tab.btn_invert_y_axis.isEnabled())
            self.assertFalse(tab.btn_fit_all.isEnabled())
            self.assertFalse(tab.btn_copy_summary.isEnabled())
            self.assertFalse(tab.btn_clear.isEnabled())
            self.assertTrue(tab.current_plot.isHidden())
            self.assertFalse(tab.chart_placeholder.isHidden())
            self.assertEqual(tab.wake_up_regions, [])
            self.assertEqual(tab.chart_time_seconds.tolist(), [])
            self.assertEqual(tab.chart_current_ma.tolist(), [])
            self.assertFalse(tab.hover_marker.isVisible())
            self.assertFalse(tab.hover_label.isVisible())
            self.assertIsNotNone(tab.upper_sleep_limit_line)
            self.assertIsNotNone(tab.lower_sleep_limit_line)
            self.assertTrue(tab.chart_scrollbar.isHidden())

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
            self.assertTrue(tab.btn_run.isEnabled())
            self.assertTrue(tab.btn_copy_data_review.isEnabled())
            self.assertTrue(tab.btn_clear.isEnabled())
            self.assertFalse(tab.btn_export.isEnabled())
            self.assertFalse(tab.btn_copy_chart.isEnabled())
            self.assertFalse(tab.btn_capture_chart.isEnabled())
            self.assertFalse(tab.btn_invert_y_axis.isEnabled())
            self.assertFalse(tab.btn_fit_all.isEnabled())
            self.assertFalse(tab.btn_copy_summary.isEnabled())
            self.assertIsNone(tab.current_curve.getData()[0])
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
            self.assertTrue(tab.btn_run.isEnabled())
            self.assertTrue(tab.btn_copy_data_review.isEnabled())
            self.assertTrue(tab.btn_clear.isEnabled())
            self.assertFalse(tab.btn_export.isEnabled())
            self.assertFalse(tab.btn_copy_chart.isEnabled())
            self.assertFalse(tab.btn_capture_chart.isEnabled())
            self.assertFalse(tab.btn_invert_y_axis.isEnabled())
            self.assertFalse(tab.btn_fit_all.isEnabled())
            self.assertFalse(tab.btn_copy_summary.isEnabled())
            warning_box.assert_not_called()

    def test_review_table_selection_clears_when_focus_leaves(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_dir = self._create_tab(tmpdir)
            tab._populate_review_table([
                type("Sample", (), {"time": "26-09-11 11:41:29.036", "current_mA": -16.9})(),
            ])

            tab.review_table.selectRow(0)
            self.assertTrue(tab.review_table.selectedItems())

            tab.review_table.focusOutEvent(QFocusEvent(QEvent.FocusOut))

            self.assertFalse(tab.review_table.selectedItems())
            self.assertEqual(tab.review_table.currentRow(), -1)

    def test_loading_selected_dataset_resets_review_scrollbar_to_top(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, database_dir = self._create_tab(tmpdir)
            first_source = Path(tmpdir) / "first.csv"
            second_source = Path(tmpdir) / "second.csv"
            first_source.write_text("Trigger time,No1 Average Ch1\n0,0.001\n", encoding="utf-8")
            second_source.write_text("Trigger time,No1 Average Ch1\n0,0.002\n", encoding="utf-8")
            first_database = database_path_for_source(first_source, database_dir)
            second_database = database_path_for_source(second_source, database_dir)
            import_dataset(
                "first",
                first_source,
                [(str(index), 0.001, 1.0) for index in range(30)],
                first_database,
            )
            import_dataset(
                "second",
                second_source,
                [(str(index), 0.002, 2.0) for index in range(30)],
                second_database,
            )
            tab._refresh_dataset_combo(selected_db_path=first_database)
            tab.import_current_file()
            scrollbar = tab.review_table.verticalScrollBar()
            scrollbar.setRange(0, 100)
            scrollbar.setValue(80)
            tab.dataset_combo.setCurrentIndex(
                tab.dataset_combo.findData(str(second_database.resolve()))
            )

            tab.import_current_file()

            self.assertEqual(tab.current_database_path, second_database.resolve())
            self.assertEqual(scrollbar.value(), scrollbar.minimum())

    def test_copy_data_review_and_summary_buttons_copy_table_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_dir = self._create_tab(tmpdir)
            tab._populate_review_table([
                type("Sample", (), {"time": "26-09-11 11:41:29.036", "current_mA": -16.9})(),
                type("Sample", (), {"time": "26-09-11 11:41:30.079", "current_mA": -17.3})(),
            ])
            tab.summary_values["sample_count"].setText("2")
            tab.summary_values["duration"].setText("1.043 s")

            tab.copy_data_review()

            self.assertEqual(
                QApplication.clipboard().text(),
                "No.\tTime\tCurrent (mA)\n"
                "1\t26-09-11 11:41:29.036\t-16.90\n"
                "2\t26-09-11 11:41:30.079\t-17.30",
            )

            tab.copy_summary()

            self.assertEqual(
                QApplication.clipboard().text(),
                "Samples\t2\n"
                "Duration\t1.043 s\n"
                f"Min Current\t{PLACEHOLDER_VALUE}\n"
                f"Max Current\t{PLACEHOLDER_VALUE}\n"
                f"Average Current\t{PLACEHOLDER_VALUE}",
            )


    def test_calculate_elapsed_seconds_uses_real_timestamp_differences(self):
        samples = [
            type("Sample", (), {"time": "26-09-11 11:41:29.036"})(),
            type("Sample", (), {"time": "26-09-11 11:41:30.079"})(),
            type("Sample", (), {"time": "26-09-11 11:41:31.150"})(),
        ]

        elapsed_seconds = calculate_elapsed_seconds(samples)

        self.assertEqual(elapsed_seconds, [0.0, 1.043, 2.114])

    def test_detect_wake_up_intervals_uses_absolute_current_and_duration(self):
        intervals = detect_wake_up_intervals(
            [0.0, 1.0, 2.0, 3.5, 5.0, 6.0, 6.5],
            [10.0, -310.0, -320.0, -450.0, 20.0, 400.0, 410.0],
            wake_limit_ma=300.0,
            wake_duration_s=2.0,
        )

        self.assertEqual(len(intervals), 1)
        self.assertEqual(intervals[0]["start_s"], 1.0)
        self.assertEqual(intervals[0]["end_s"], 3.5)
        self.assertEqual(intervals[0]["duration_s"], 2.5)
        self.assertEqual(intervals[0]["peak_current_ma"], 450.0)

    def test_run_draws_current_chart_thresholds_and_enables_chart_actions(self):
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
                    ("26-09-11 11:41:31.150", -0.0181, -18.1),
                ],
                database_file,
            )
            tab._refresh_dataset_combo(selected_db_path=database_file)
            tab.import_current_file()

            tab.btn_run.click()

            current_x, current_y = tab.current_curve.getData()
            self.assertEqual([round(value, 3) for value in current_x.tolist()], [0.0, 1.043, 2.114])
            self.assertEqual([round(value, 2) for value in current_y.tolist()], [-16.9, -17.3, -18.1])
            self.assertEqual(tab.upper_sleep_limit_line.value(), tab.current_limit_edit.value())
            self.assertEqual(tab.lower_sleep_limit_line.value(), -tab.current_limit_edit.value())
            self.assertFalse(tab.upper_sleep_limit_line.movable)
            self.assertFalse(tab.lower_sleep_limit_line.movable)
            self.assertEqual(tab.wake_up_regions, [])
            self.assertEqual(self._legend_labels(tab), [
                "Current",
                "Sleep threshold",
                "Wake-up",
            ])
            self.assertIsNone(tab.current_plot.getPlotItem().legend)
            self.assertTrue(tab.btn_export.isEnabled())
            self.assertTrue(tab.btn_copy_chart.isEnabled())
            self.assertTrue(tab.btn_capture_chart.isEnabled())
            self.assertTrue(tab.btn_invert_y_axis.isEnabled())
            self.assertTrue(tab.btn_fit_all.isEnabled())
            self.assertTrue(tab.btn_copy_summary.isEnabled())
            self.assertFalse(tab.current_plot.isHidden())
            self.assertTrue(tab.chart_placeholder.isHidden())
            self.assertTrue(tab.chart_scrollbar.isHidden())
            self.assertEqual(tab.analysis_result_edit.text(), "RUN")
            self.assertEqual(tab.chart_time_seconds.tolist(), [0.0, 1.043, 2.114])
            self.assertEqual(tab.chart_current_ma.tolist(), [-16.9, -17.3, -18.1])
            bottom_axis = tab.current_plot.getPlotItem().getAxis("bottom")
            left_axis = tab.current_plot.getPlotItem().getAxis("left")
            self.assertEqual(bottom_axis.labelText, "Time (s)")
            self.assertEqual(left_axis.labelText, "Current (mA)")
            self.assertFalse(getattr(bottom_axis, "autoSIPrefix", True))
            self.assertFalse(getattr(left_axis, "autoSIPrefix", True))

    def test_long_time_range_uses_horizontal_chart_scrollbar(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, database_dir = self._create_tab(tmpdir)
            source_file = Path(tmpdir) / "long_sample.csv"
            source_file.write_text("Trigger time,No1 Average Ch1\n0,0.001\n", encoding="utf-8")
            database_file = database_path_for_source(source_file, database_dir)
            import_dataset(
                "long_sample",
                source_file,
                [(str(seconds), 0.001, float(index)) for index, seconds in enumerate((0, 200, 400, 600, 800))],
                database_file,
            )
            tab._refresh_dataset_combo(selected_db_path=database_file)
            tab.import_current_file()

            tab.btn_run.click()

            self.assertFalse(tab.chart_scrollbar.isHidden())
            self.assertGreater(tab.chart_scrollbar.maximum(), 0)
            tab.chart_scrollbar.setValue(tab.chart_scrollbar.maximum())

            start_range, end_range = tab.current_plot.getPlotItem().viewRange()[0]
            self.assertAlmostEqual(start_range, 400.0, places=3)
            self.assertAlmostEqual(end_range, 800.0, places=3)

    def test_run_highlights_wake_up_regions_and_keeps_signed_current_curve(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_dir = self._create_tab(tmpdir)
            tab.wake_limit_edit.setValue(300.0)
            tab.wake_duration_edit.setValue(2.0)
            tab._load_samples_into_workspace([
                self._sample(0.0, 10.0),
                self._sample(1.0, -310.0),
                self._sample(2.0, -320.0),
                self._sample(3.5, -450.0),
                self._sample(5.0, 20.0),
                self._sample(6.0, 350.0),
                self._sample(6.5, 360.0),
            ])

            tab.btn_run.click()

            current_x, current_y = tab.current_curve.getData()
            self.assertEqual(current_x.tolist(), [0.0, 1.0, 2.0, 3.5, 5.0, 6.0, 6.5])
            self.assertEqual(current_y.tolist(), [10.0, -310.0, -320.0, -450.0, 20.0, 350.0, 360.0])
            self.assertEqual(len(tab.wake_up_regions), 1)
            self.assertEqual(tab.wake_up_regions[0].getRegion(), (1.0, 3.5))
            self.assertEqual(tab.wake_up_regions[0].zValue(), -10)
            self.assertFalse(tab.wake_up_regions[0].movable)

            ThemeManager.fn_set_theme(ThemeType.DARK)
            tab.fn_refresh_theme()

            self.assertEqual(len(tab.wake_up_regions), 1)
            self.assertEqual(tab.wake_up_regions[0].getRegion(), (1.0, 3.5))
            themed_x, themed_y = tab.current_curve.getData()
            self.assertEqual(themed_x.tolist(), current_x.tolist())
            self.assertEqual(themed_y.tolist(), current_y.tolist())

    def test_sleep_limit_change_updates_existing_lines_and_marks_not_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_dir = self._create_tab(tmpdir)
            tab._load_samples_into_workspace([
                self._sample(0.0, 1.0),
                self._sample(1.0, -2.0),
            ])
            tab.btn_run.click()
            upper_line = tab.upper_sleep_limit_line
            lower_line = tab.lower_sleep_limit_line

            tab.current_limit_edit.setValue(45.0)

            self.assertIs(tab.upper_sleep_limit_line, upper_line)
            self.assertIs(tab.lower_sleep_limit_line, lower_line)
            self.assertEqual(tab.upper_sleep_limit_line.value(), 45.0)
            self.assertEqual(tab.lower_sleep_limit_line.value(), -45.0)
            self.assertEqual(tab.analysis_result_edit.text(), "NOT RUN")

    def test_hover_uses_nearest_sample_without_changing_current_sign(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_dir = self._create_tab(tmpdir)
            tab._load_samples_into_workspace([
                self._sample(0.0, 10.0),
                self._sample(1.5, -28.46),
                self._sample(3.0, 12.0),
            ])
            tab.btn_run.click()

            nearest = tab.find_nearest_sample(1.6)
            self.assertEqual(nearest, (1.5, -28.46))

            tab.update_hover_items(*nearest)

            marker_x, marker_y = tab.hover_marker.getData()
            self.assertEqual(marker_x.tolist(), [1.5])
            self.assertEqual(marker_y.tolist(), [-28.46])
            self.assertTrue(tab.hover_marker.isVisible())
            self.assertFalse(hasattr(tab, "chart_coordinate_label"))
            hover_html = tab.hover_label.toHtml().replace("\xa0", " ")
            self.assertIn("Time: 1.500 s", hover_html)
            self.assertIn("Current: -28.46 mA", hover_html)

    def test_chart_uses_custom_pin_context_menu_without_default_pyqtgraph_menu(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_dir = self._create_tab(tmpdir)
            view_box = tab.current_plot.getPlotItem().getViewBox()

            self.assertFalse(view_box.menuEnabled())
            self.assertEqual(tab._chart_context_action_at_scene_position(None), (None, None))

    def test_chart_pin_context_adds_multiple_pins_prevents_duplicates_and_deletes_one(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_dir = self._create_tab(tmpdir)
            tab._load_samples_into_workspace([
                self._sample(0.0, 10.0),
                self._sample(1.5, -28.46),
                self._sample(3.0, 12.0),
            ])
            tab.btn_run.click()

            first_scene_pos = tab._scene_position_for_chart_sample(1)
            action, payload = tab._chart_context_action_at_scene_position(first_scene_pos)
            self.assertEqual(action, "pin")
            self.assertEqual(payload, 1)
            menu, _primary_action, clear_action = tab._create_chart_context_menu(action)
            self.assertEqual(
                [item.text() for item in menu.actions() if not item.isSeparator()],
                ["Pin"],
            )
            self.assertIsNone(clear_action)

            self.assertTrue(tab.pin_chart_sample(payload))
            self.assertEqual(len(tab.chart_pins), 1)
            self.assertEqual(tab.chart_pins[0].sample_index, 1)
            self.assertEqual(tab.chart_pins[0].time_s, 1.5)
            self.assertEqual(tab.chart_pins[0].current_ma, -28.46)
            pin_html = tab.chart_pins[0].label.toHtml().replace("\xa0", " ")
            self.assertIn("Time: 1.500 s", pin_html)
            self.assertIn("Current: -28.46 mA", pin_html)

            action, payload = tab._chart_context_action_at_scene_position(first_scene_pos)
            self.assertEqual(action, "delete")
            self.assertIs(payload, tab.chart_pins[0])
            menu, _primary_action, clear_action = tab._create_chart_context_menu(action)
            self.assertEqual(
                ["---" if item.isSeparator() else item.text() for item in menu.actions()],
                ["Delete Pin", "---", "Clear All Pins"],
            )
            self.assertIsNotNone(clear_action)
            self.assertFalse(tab.pin_chart_sample(1))
            self.assertEqual(len(tab.chart_pins), 1)

            normal_scene_pos = tab._scene_position_for_chart_sample(0)
            action, normal_payload = tab._chart_context_action_at_scene_position(normal_scene_pos)
            self.assertEqual(action, "pin")
            self.assertEqual(normal_payload, 0)
            menu, _primary_action, clear_action = tab._create_chart_context_menu(action)
            self.assertEqual(
                ["---" if item.isSeparator() else item.text() for item in menu.actions()],
                ["Pin", "---", "Clear All Pins"],
            )
            self.assertIsNotNone(clear_action)

            self.assertTrue(tab.pin_chart_sample(2))
            self.assertEqual(len(tab.chart_pins), 2)
            tab.hide_hover_items()
            self.assertEqual(len(tab.chart_pins), 2)

            tab.delete_chart_pin(payload)

            self.assertEqual(len(tab.chart_pins), 1)
            self.assertEqual(tab.chart_pins[0].sample_index, 2)
            self.assertEqual(tab.chart_current_ma.tolist(), [10.0, -28.46, 12.0])
            self.assertEqual(
                [sample.current_mA for sample in tab.current_samples],
                [10.0, -28.46, 12.0],
            )

    def test_chart_pins_survive_view_actions_and_clear_with_workspace(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_dir = self._create_tab(tmpdir)
            tab._load_samples_into_workspace([
                self._sample(0.0, -25.0),
                self._sample(100.0, 10.0),
                self._sample(200.0, 80.0),
            ])
            tab.btn_run.click()
            tab.pin_chart_sample(0)
            tab.pin_chart_sample(2)

            tab.btn_invert_y_axis.click()
            tab.current_plot.setXRange(40.0, 60.0, padding=0)
            tab.btn_fit_all.click()

            self.assertEqual([pin.sample_index for pin in tab.chart_pins], [0, 2])
            self.assertTrue(tab.current_plot.getPlotItem().getViewBox().yInverted())
            first_pin_html = tab.chart_pins[0].label.toHtml().replace("\xa0", " ")
            self.assertIn("Current: -25.00 mA", first_pin_html)

            menu, primary_action, clear_action = tab._create_chart_context_menu("pin")
            tab._apply_chart_context_menu_selection(
                clear_action,
                primary_action,
                clear_action,
                "pin",
                1,
            )
            self.assertEqual(tab.chart_pins, [])
            self.assertFalse(tab.current_plot.isHidden())
            self.assertEqual(tab.chart_time_seconds.tolist(), [0.0, 100.0, 200.0])
            self.assertEqual(tab.chart_current_ma.tolist(), [-25.0, 10.0, 80.0])
            tab.update_hover_items(100.0, 10.0)
            self.assertTrue(tab.hover_label.isVisible())
            tab.btn_fit_all.click()
            tab.btn_invert_y_axis.click()
            self.assertFalse(tab.current_plot.getPlotItem().getViewBox().yInverted())
            self.assertTrue(tab.capture_current_chart())
            self.assertTrue(tab.pin_chart_sample(1))
            self.assertEqual([pin.sample_index for pin in tab.chart_pins], [1])

            tab._load_samples_into_workspace([
                self._sample(0.0, 1.0),
                self._sample(1.0, 2.0),
            ])
            self.assertEqual(tab.chart_pins, [])

            tab.btn_run.click()
            tab.pin_chart_sample(1)
            self.assertEqual(len(tab.chart_pins), 1)
            tab.btn_clear.click()
            self.assertEqual(tab.chart_pins, [])

    def test_chart_pin_theme_refresh_updates_existing_pin_label(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_dir = self._create_tab(tmpdir)
            tab._load_samples_into_workspace([
                self._sample(0.0, 1.0),
                self._sample(1.0, 2.0),
            ])
            tab.btn_run.click()
            tab.pin_chart_sample(1)
            light_html = tab.chart_pins[0].label.toHtml()

            ThemeManager.fn_set_theme(ThemeType.DARK)
            tab.fn_refresh_theme()
            dark_html = tab.chart_pins[0].label.toHtml()

            self.assertNotEqual(light_html, dark_html)
            self.assertIn(ThemeManager.fn_colors().TEXT.lower(), dark_html.lower())

    def test_invert_y_axis_toggles_viewbox_without_changing_chart_data_or_hover(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_dir = self._create_tab(tmpdir)
            tab._load_samples_into_workspace([
                self._sample(0.0, -25.30),
                self._sample(1.0, 42.0),
            ])
            tab.btn_run.click()
            view_box = tab.current_plot.getPlotItem().getViewBox()
            x_range_before = tab.current_plot.getPlotItem().viewRange()[0]
            current_x, current_y = tab.current_curve.getData()

            tab.btn_invert_y_axis.click()

            self.assertTrue(tab._y_axis_inverted)
            self.assertTrue(view_box.yInverted())
            self.assertEqual(tab.current_curve.getData()[0].tolist(), current_x.tolist())
            self.assertEqual(tab.current_curve.getData()[1].tolist(), current_y.tolist())
            self.assertEqual(tab.chart_current_ma.tolist(), [-25.30, 42.0])
            self.assertEqual(tab.current_samples[0].current_mA, -25.30)
            self.assertEqual(tab.current_plot.getPlotItem().viewRange()[0], x_range_before)

            tab.update_hover_items(0.0, -25.30)
            hover_html = tab.hover_label.toHtml().replace("\xa0", " ")
            self.assertIn("Current: -25.30 mA", hover_html)

            tab.btn_invert_y_axis.click()

            self.assertFalse(tab._y_axis_inverted)
            self.assertFalse(view_box.yInverted())
            self.assertEqual(tab.chart_current_ma.tolist(), [-25.30, 42.0])

    def test_fit_all_restores_full_chart_view_without_resetting_inverted_y(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_dir = self._create_tab(tmpdir)
            tab._load_samples_into_workspace([
                self._sample(0.0, -25.0),
                self._sample(100.0, 10.0),
                self._sample(200.0, 80.0),
            ])
            tab.btn_run.click()
            tab.btn_invert_y_axis.click()
            tab.current_plot.setXRange(40.0, 60.0, padding=0)
            tab.current_plot.setYRange(-5.0, 5.0, padding=0)

            tab.btn_fit_all.click()

            x_range, y_range = tab.current_plot.getPlotItem().viewRange()
            self.assertLessEqual(x_range[0], 0.0)
            self.assertGreaterEqual(x_range[1], 200.0)
            self.assertLessEqual(y_range[0], -25.0)
            self.assertGreaterEqual(y_range[1], 80.0)
            self.assertTrue(tab._y_axis_inverted)
            self.assertTrue(tab.current_plot.getPlotItem().getViewBox().yInverted())
            self.assertEqual(tab.chart_time_seconds.tolist(), [0.0, 100.0, 200.0])
            self.assertEqual(tab.chart_current_ma.tolist(), [-25.0, 10.0, 80.0])

    def test_clear_and_new_dataset_reset_y_axis_orientation_and_disable_chart_actions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_dir = self._create_tab(tmpdir)
            tab._load_samples_into_workspace([
                self._sample(0.0, 1.0),
                self._sample(1.0, 2.0),
            ])
            tab.btn_run.click()
            tab.btn_invert_y_axis.click()
            self.assertTrue(tab.current_plot.getPlotItem().getViewBox().yInverted())

            tab._load_samples_into_workspace([
                self._sample(0.0, -3.0),
                self._sample(1.0, -4.0),
            ])

            self.assertFalse(tab._y_axis_inverted)
            self.assertFalse(tab.current_plot.getPlotItem().getViewBox().yInverted())
            self.assertFalse(tab.btn_invert_y_axis.isEnabled())
            self.assertFalse(tab.btn_fit_all.isEnabled())
            self.assertFalse(tab.btn_capture_chart.isEnabled())

            tab.btn_run.click()
            tab.btn_invert_y_axis.click()
            tab.btn_clear.click()

            self.assertFalse(tab._y_axis_inverted)
            self.assertFalse(tab.current_plot.getPlotItem().getViewBox().yInverted())
            self.assertFalse(tab.btn_invert_y_axis.isEnabled())
            self.assertFalse(tab.btn_fit_all.isEnabled())
            self.assertFalse(tab.btn_capture_chart.isEnabled())

    def test_capture_buttons_copy_current_chart_pixmap_to_clipboard(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, _database_dir = self._create_tab(tmpdir)
            tab._load_samples_into_workspace([
                self._sample(0.0, 1.0),
                self._sample(1.0, -2.0),
            ])
            self.assertFalse(tab.capture_current_chart())

            tab.btn_run.click()
            tab.btn_invert_y_axis.click()

            self.assertTrue(tab.capture_current_chart())
            first_pixmap = QApplication.clipboard().pixmap()
            self.assertFalse(first_pixmap.isNull())

            QApplication.clipboard().clear()
            tab.btn_capture_chart.click()
            capture_pixmap = QApplication.clipboard().pixmap()
            self.assertFalse(capture_pixmap.isNull())

            QApplication.clipboard().clear()
            tab.btn_copy_chart.click()
            copy_pixmap = QApplication.clipboard().pixmap()
            self.assertFalse(copy_pixmap.isNull())
            self.assertTrue(tab.current_plot.getPlotItem().getViewBox().yInverted())
            self.assertEqual(tab.chart_current_ma.tolist(), [1.0, -2.0])

    def test_run_again_refreshes_chart_without_duplicate_items_and_updates_thresholds(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, database_dir = self._create_tab(tmpdir)
            source_file = Path(tmpdir) / "sample.csv"
            source_file.write_text("Trigger time,No1 Average Ch1\n0,0.001\n", encoding="utf-8")
            database_file = database_path_for_source(source_file, database_dir)
            import_dataset(
                "sample",
                source_file,
                [("0", 0.001, 1.0), ("1.5", 0.002, 2.0)],
                database_file,
            )
            tab._refresh_dataset_combo(selected_db_path=database_file)
            tab.import_current_file()

            tab.btn_run.click()
            current_curve = tab.current_curve
            upper_line = tab.upper_sleep_limit_line
            lower_line = tab.lower_sleep_limit_line
            hover_marker = tab.hover_marker
            tab.current_limit_edit.setValue(45.0)
            tab.wake_limit_edit.setValue(350.0)
            tab.btn_run.click()

            self.assertIs(tab.current_curve, current_curve)
            self.assertIs(tab.upper_sleep_limit_line, upper_line)
            self.assertIs(tab.lower_sleep_limit_line, lower_line)
            self.assertIs(tab.hover_marker, hover_marker)
            self.assertEqual(len(self._legend_labels(tab)), 3)
            self.assertEqual(tab.upper_sleep_limit_line.value(), 45.0)
            self.assertEqual(tab.lower_sleep_limit_line.value(), -45.0)
            current_x, current_y = tab.current_curve.getData()
            self.assertEqual(current_x.tolist(), [0.0, 1.5])
            self.assertEqual(current_y.tolist(), [1.0, 2.0])

    def test_clear_resets_workspace_without_deleting_database_or_combo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tab, database_dir = self._create_tab(tmpdir)
            source_file = Path(tmpdir) / "sample.csv"
            source_file.write_text("Trigger time,No1 Average Ch1\n0,0.001\n", encoding="utf-8")
            database_file = database_path_for_source(source_file, database_dir)
            import_dataset(
                "sample",
                source_file,
                [("0", 0.001, 1.0), ("1", 0.002, 2.0)],
                database_file,
            )
            tab._refresh_dataset_combo(selected_db_path=database_file)
            tab.import_current_file()
            tab.btn_run.click()

            tab.btn_clear.click()

            self.assertTrue(database_file.exists())
            self.assertEqual(tab.dataset_combo.count(), 1)
            self.assertEqual(tab.current_samples, [])
            self.assertEqual(tab.review_table.rowCount(), 0)
            self.assertIsNone(tab.current_curve.getData()[0])
            self.assertEqual(tab.analysis_result_edit.text(), "NOT RUN")
            self.assertFalse(tab.btn_run.isEnabled())
            self.assertFalse(tab.btn_copy_data_review.isEnabled())
            self.assertFalse(tab.btn_export.isEnabled())
            self.assertFalse(tab.btn_copy_chart.isEnabled())
            self.assertFalse(tab.btn_capture_chart.isEnabled())
            self.assertFalse(tab.btn_invert_y_axis.isEnabled())
            self.assertFalse(tab.btn_fit_all.isEnabled())
            self.assertFalse(tab.btn_copy_summary.isEnabled())
            self.assertFalse(tab.btn_clear.isEnabled())
            self.assertTrue(tab.current_plot.isHidden())
            self.assertFalse(tab.chart_placeholder.isHidden())
            self.assertEqual(tab.wake_up_regions, [])
            self.assertEqual(tab.chart_time_seconds.tolist(), [])
            self.assertEqual(tab.chart_current_ma.tolist(), [])
            self.assertFalse(tab.hover_marker.isVisible())
            self.assertFalse(tab.hover_label.isVisible())
            self.assertIsNotNone(tab.upper_sleep_limit_line)
            self.assertIsNotNone(tab.lower_sleep_limit_line)

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
                tab.btn_copy_data_review,
                tab.btn_copy_summary,
                tab.btn_clear,
            ]
            self.assertTrue(all(isinstance(button, PrimaryButton) for button in buttons))
            self.assertEqual([button.text() for button in buttons], [
                "RUN",
                "EXPORT",
                "COPY CHART",
                "COPY Data Review",
                "COPY Summary",
                "CLEAR",
            ])
            chart_buttons = [
                tab.btn_invert_y_axis,
                tab.btn_fit_all,
                tab.btn_capture_chart,
            ]
            self.assertTrue(all(isinstance(button, QuickAccessButton) for button in chart_buttons))
            self.assertEqual([button.text() for button in chart_buttons], [
                "Invert Y Axis",
                "Fit All",
                "Capture",
            ])
            self.assertLess(
                tab.legend_layout.indexOf(tab.btn_invert_y_axis),
                tab.legend_layout.indexOf(tab.btn_fit_all),
            )
            self.assertLess(
                tab.legend_layout.indexOf(tab.btn_fit_all),
                tab.legend_layout.indexOf(tab.btn_capture_chart),
            )
            self.assertTrue(tab.dataset_combo.view().verticalScrollBar().styleSheet())
            self.assertTrue(tab.chart_scrollbar.styleSheet())

            light_style = tab.chart_placeholder.styleSheet()
            light_quick_access_style = tab.btn_fit_all.styleSheet()
            ThemeManager.fn_set_theme(ThemeType.DARK)
            tab.fn_refresh_theme()
            dark_style = tab.chart_placeholder.styleSheet()
            dark_quick_access_style = tab.btn_fit_all.styleSheet()

            self.assertNotEqual(light_style, dark_style)
            self.assertNotEqual(light_quick_access_style, dark_quick_access_style)
            self.assertIn(ThemeManager.fn_colors().TEXT, dark_style)
            self.assertTrue(tab.current_limit_edit.styleSheet())
            self.assertEqual(
                tab.current_limit_edit.styleSheet(),
                tab.wake_limit_edit.styleSheet(),
            )
            self.assertEqual(
                tab.current_limit_edit.styleSheet(),
                tab.wake_duration_edit.styleSheet(),
            )


if __name__ == "__main__":
    unittest.main()
