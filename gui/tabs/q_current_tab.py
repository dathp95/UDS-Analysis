from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from datetime import datetime
from pathlib import Path

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QScrollBar,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QHeaderView,
    QMenu,
)

from core.q_current_analysis import analyze_q_current, parse_q_current_timestamp
from core.q_current_config import QCurrentConfig, load_q_current_config, save_q_current_config
from core.q_current_report_export import QCurrentReportData, QCurrentReportSettings
from core.services.q_current_report_service import QCurrentReportService
from core.sleep_current_database import (
    database_path_for_source,
    default_dataset_name,
    ensure_database_directory,
    get_primary_dataset,
    get_samples,
    import_dataset,
    list_datasets,
    normalize_current_data,
)
from gui.themes.styles.containers.groupbox_style import fn_groupbox_style
from gui.themes.styles.controls.scrollbar_style import (
    fn_apply_scrollbar_style,
    fn_scrollbar_style,
)
from gui.themes.styles.controls.spinbox_style import fn_spinbox_style
from gui.themes.theme_manager import ThemeManager
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_combobox import PrimaryComboBox
from gui.widgets.controls.primary_label import PrimaryLabel
from gui.widgets.controls.primary_lineedit import PrimaryLineEdit
from gui.widgets.controls.primary_table import PrimaryTable
from gui.widgets.controls.quick_access_button import QuickAccessButton
from gui.widgets.q_current.summary_widget import QCurrentSummaryWidget


PLACEHOLDER_VALUE = "\u2014"
SOURCE_FILE_PLACEHOLDER = "Select current data file (*.csv, *.xlsx)"
SUPPORTED_SOURCE_EXTENSIONS = {".csv", ".xlsx"}
SOURCE_FILE_FILTER = (
    "Supported Files (*.csv *.xlsx);;"
    "CSV Files (*.csv);;"
    "Excel Files (*.xlsx)"
)
CHART_SCROLL_VISIBLE_SECONDS = 400.0
CHART_SCROLL_SCALE = 1000
PIN_HIT_RADIUS_PX = 12.0
SAMPLE_HIT_RADIUS_PX = 18.0


def parse_timestamp(value):
    return parse_q_current_timestamp(value)


def calculate_elapsed_seconds(samples):
    parsed_values = [parse_timestamp(sample.time) for sample in samples]
    if not parsed_values:
        return []
    first_value = parsed_values[0]
    elapsed_seconds = []
    for parsed_value in parsed_values:
        if isinstance(first_value, datetime) and isinstance(parsed_value, datetime):
            elapsed_seconds.append((parsed_value - first_value).total_seconds())
        elif not isinstance(first_value, datetime) and not isinstance(parsed_value, datetime):
            elapsed_seconds.append(float(parsed_value) - float(first_value))
        else:
            raise ValueError("Current data contains mixed timestamp formats")
    return elapsed_seconds



@dataclass
class ChartPin:
    sample_index: int
    time_s: float
    current_ma: float
    marker: pg.ScatterPlotItem
    label: pg.TextItem


class QCurrentDatasetComboBox(PrimaryComboBox):

    def __init__(self, refresh_callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._refresh_callback = refresh_callback
        self._refresh_popup_scrollbar()

    def showPopup(self):
        self._refresh_callback()
        self._refresh_popup_scrollbar()
        super().showPopup()

    def fn_refresh_theme(self):
        super().fn_refresh_theme()
        self._refresh_popup_scrollbar()

    def _refresh_popup_scrollbar(self):
        fn_apply_scrollbar_style(self.view())


class QCurrentReviewTable(PrimaryTable):

    def focusOutEvent(self, event):
        self.clearSelection()
        self.setCurrentCell(-1, -1)
        super().focusOutEvent(event)


class QCurrentTab(QWidget):

    def __init__(
        self,
        database_dir: str | Path | None = None,
        config_file: str | Path | None = None,
    ):
        super().__init__()

        self._theme_widgets = []
        self._database_dir = database_dir
        self._config_file = config_file
        self.q_current_config = load_q_current_config(config_file)
        self.current_import = None
        self.current_samples = []
        self.current_database_path = None
        self.current_analysis_result = None
        self.current_analysis_settings = None
        self.q_current_report_service = QCurrentReportService()
        self._chart_ready = False
        self.current_curve = None
        self.upper_sleep_limit_line = None
        self.lower_sleep_limit_line = None
        self.hover_marker = None
        self.hover_label = None
        self.wake_up_regions = []
        self.chart_pins = []
        self.chart_time_seconds = np.array([], dtype=float)
        self.chart_current_ma = np.array([], dtype=float)
        self._hover_sample = None
        self._y_axis_inverted = False
        self._chart_scrollbar_updating = False
        self._chart_x_min = 0.0
        self._chart_x_max = 0.0
        self._chart_visible_span = CHART_SCROLL_VISIBLE_SECONDS
        self._setup_ui()
        self._initialize_database()
        self._connect_signals()
        self.fn_refresh_theme()
        self._update_action_states()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        self.settings_group = self._create_settings_group()
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)

        self.review_group = self._create_review_group()
        self.chart_group = self._create_chart_group()
        self.right_panel = self._create_right_panel()

        self.main_splitter.addWidget(self.review_group)
        self.main_splitter.addWidget(self.chart_group)
        self.main_splitter.addWidget(self.right_panel)
        self.main_splitter.setSizes([260, 720, 220])

        main_layout.addWidget(self.settings_group)
        main_layout.addWidget(self.main_splitter, 1)

    def _initialize_database(self):
        ensure_database_directory(self._database_dir)

    def _connect_signals(self):
        self.browse_button.clicked.connect(self.browse_current_file)
        self.import_button.clicked.connect(self.import_current_file)
        self.btn_run.clicked.connect(self.run_current_analysis)
        self.btn_export.clicked.connect(self.export_q_current_report)
        self.btn_clear.clicked.connect(self.clear_current_workspace)
        self.save_config_button.clicked.connect(self.save_current_config)
        self.btn_capture_chart.clicked.connect(self.capture_current_chart)
        self.btn_invert_y_axis.clicked.connect(self.toggle_y_axis_inversion)
        self.btn_fit_all.clicked.connect(self._fit_all_current_chart)
        self.current_plot.customContextMenuRequested.connect(
            self.show_chart_context_menu
        )
        self.btn_copy_data_review.clicked.connect(self.copy_data_review)
        self.btn_copy_summary.clicked.connect(self.copy_summary)
        self.chart_scrollbar.valueChanged.connect(
            self._on_chart_scrollbar_changed
        )
        self.current_limit_edit.valueChanged.connect(
            self.update_sleep_limit_lines
        )
        self.wake_limit_edit.valueChanged.connect(self._mark_analysis_not_run)
        self.wake_duration_edit.valueChanged.connect(self._mark_analysis_not_run)

    def _create_settings_group(self):
        group = QGroupBox("Analysis Settings")

        self.settings_layout = QGridLayout(group)
        self.settings_layout.setContentsMargins(12, 16, 12, 12)
        self.settings_layout.setHorizontalSpacing(8)
        self.settings_layout.setVerticalSpacing(8)

        self.source_file_edit = PrimaryLineEdit(
            placeholder=SOURCE_FILE_PLACEHOLDER,
        )
        self.source_file_edit.setObjectName("source_file_edit")
        self.source_file_edit.setReadOnly(True)
        self.source_file_edit.setToolTip("")

        self.browse_button = PrimaryButton(
            "Browse",
            width=90,
            height=36,
        )
        self.browse_button.setObjectName("browse_button")

        self.dataset_combo = QCurrentDatasetComboBox(self._refresh_dataset_combo)
        self.dataset_combo.setObjectName("dataset_combo")
        self.dataset_combo.setMinimumWidth(220)
        self.dataset_combo.setFixedHeight(36)

        self.import_button = PrimaryButton(
            "Import",
            width=90,
            height=36,
        )
        self.import_button.setObjectName("import_button")
        self.import_button.setEnabled(True)

        self.current_limit_label = PrimaryLabel(
            "Sleep limit (mA)"
        )

        self.current_limit_edit = QDoubleSpinBox()
        self.current_limit_edit.setObjectName("current_limit_edit")
        self.current_limit_edit.setDecimals(1)
        self.current_limit_edit.setMinimum(0.0)
        self.current_limit_edit.setMaximum(1000000.0)
        self.current_limit_edit.setSingleStep(0.5)
        self.current_limit_edit.setValue(self.q_current_config.standard_current_ma)
        self.current_limit_edit.setFixedWidth(110)
        self.current_limit_edit.setMinimumHeight(36)
        self.current_limit_edit.lineEdit().setAlignment(Qt.AlignCenter)


        self.wake_limit_label = PrimaryLabel(
            "Wake Up limit (mA)"
        )

        self.wake_limit_edit = QDoubleSpinBox()
        self.wake_limit_edit.setObjectName("wake_limit_edit")
        self.wake_limit_edit.setDecimals(1)
        self.wake_limit_edit.setMinimum(0.0)
        self.wake_limit_edit.setMaximum(1000000.0)
        self.wake_limit_edit.setSingleStep(0.5)
        self.wake_limit_edit.setValue(self.q_current_config.wake_up_limit_ma)
        self.wake_limit_edit.setFixedWidth(110)
        self.wake_limit_edit.setMinimumHeight(36)
        self.wake_limit_edit.lineEdit().setAlignment(Qt.AlignCenter)

        self.wake_duration_label = PrimaryLabel(
            "Wake duration (s)"
        )

        self.wake_duration_edit = QDoubleSpinBox()
        self.wake_duration_edit.setObjectName("wake_duration_edit")
        self.wake_duration_edit.setDecimals(1)
        self.wake_duration_edit.setMinimum(0.1)
        self.wake_duration_edit.setMaximum(3600.0)
        self.wake_duration_edit.setSingleStep(0.5)
        self.wake_duration_edit.setValue(self.q_current_config.wake_duration_s)
        self.wake_duration_edit.setFixedWidth(90)
        self.wake_duration_edit.setMinimumHeight(36)
        self.wake_duration_edit.lineEdit().setAlignment(Qt.AlignCenter)

        self.save_config_button = PrimaryButton(
            "SAVE CONFIG",
            width=120,
            height=36,
        )
        self.save_config_button.setObjectName("save_config_button")

        self.analysis_result_label = PrimaryLabel(
            "Analysis result:"
        )

        self.analysis_result_edit = PrimaryLineEdit()
        self.analysis_result_edit.setObjectName(
            "analysis_result_edit"
        )
        self.analysis_result_edit.setReadOnly(True)
        self._set_analysis_result("NOT RUN")
        self.analysis_result_edit.setFixedWidth(130)

        self.settings_layout.addWidget(self.source_file_edit, 0, 0)
        self.settings_layout.addWidget(self.browse_button, 0, 1)
        self.settings_layout.addWidget(self.dataset_combo, 0, 2)
        self.settings_layout.addWidget(self.import_button, 0, 3)
        self.settings_layout.setColumnStretch(0, 1)

        result_layout = QHBoxLayout()
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_layout.setSpacing(8)
        result_layout.addWidget(self.current_limit_label)
        result_layout.addWidget(self.current_limit_edit)
        result_layout.addSpacing(16)

        result_layout.addWidget(self.wake_limit_label)
        result_layout.addWidget(self.wake_limit_edit)
        result_layout.addSpacing(16)
        result_layout.addWidget(self.wake_duration_label)
        result_layout.addWidget(self.wake_duration_edit)
        result_layout.addSpacing(16)
        result_layout.addWidget(self.save_config_button)
        result_layout.addSpacing(16)
        result_layout.addWidget(self.analysis_result_label)
        result_layout.addWidget(self.analysis_result_edit)
        result_layout.addStretch(1)

        self.settings_layout.addLayout(result_layout, 1, 0, 1, 4)

        return group

    def _create_chart_group(self):
        group = QGroupBox("Current Chart")
        self.chart_layout = QVBoxLayout(group)
        self.chart_layout.setContentsMargins(12, 16, 12, 12)
        self.chart_layout.setSpacing(8)

        self.legend_layout = QHBoxLayout()
        self.legend_layout.setContentsMargins(0, 0, 0, 0)
        self.legend_layout.setSpacing(18)
        self.legend_items = self._create_chart_legend_items()
        for legend_item in self.legend_items:
            self.legend_layout.addWidget(legend_item)
        self.legend_layout.addStretch(1)
        self.btn_invert_y_axis = QuickAccessButton(
            "Invert Y Axis",
            width=120,
            height=30,
        )
        self.btn_invert_y_axis.setObjectName("btn_invert_y_axis")
        self.btn_fit_all = QuickAccessButton(
            "Fit All",
            width=80,
            height=30,
        )
        self.btn_fit_all.setObjectName("btn_fit_all")
        self.btn_capture_chart = QuickAccessButton(
            "Capture",
            width=90,
            height=30,
        )
        self.btn_capture_chart.setObjectName("btn_capture_chart")
        self.legend_layout.addWidget(self.btn_invert_y_axis)
        self.legend_layout.addWidget(self.btn_fit_all)
        self.legend_layout.addWidget(self.btn_capture_chart)
       
        self.chart_content_layout = QVBoxLayout()
        self.chart_content_layout.setContentsMargins(0, 0, 0, 0)
        self.chart_placeholder = self._create_placeholder_panel()
        self.current_plot = self._create_current_plot()
        self.current_plot.hide()
        self.chart_content_layout.addWidget(self.chart_placeholder, 1)
        self.chart_content_layout.addWidget(self.current_plot, 1)

        self.chart_scrollbar = QScrollBar(Qt.Horizontal)
        self.chart_scrollbar.setObjectName("chart_scrollbar")
        self.chart_scrollbar.setSingleStep(CHART_SCROLL_SCALE)
        self.chart_scrollbar.setPageStep(
            int(CHART_SCROLL_VISIBLE_SECONDS * CHART_SCROLL_SCALE)
        )
        self.chart_scrollbar.hide()
        self.chart_content_layout.addWidget(self.chart_scrollbar)

        self.chart_layout.addLayout(self.legend_layout)
        self.chart_layout.addLayout(self.chart_content_layout, 1)
        return group

    def _create_chart_legend_items(self):
        return [
            self._create_legend_item(
                "Current",
                "line-solid",
                "Gia tri dong dien thuc te",
            ),
            self._create_legend_item(
                "Sleep threshold",
                "line-dashed",
                "Nguong dong ngu do nguoi dung cai dat",
            ),
            self._create_legend_item(
                "Wake-up",
                "dot",
                "Nguong tham chieu wake-up",
            ),
        ]

    def _create_legend_item(self, text, marker_type, tooltip):
        item = QWidget()
        item.setToolTip(tooltip)
        layout = QHBoxLayout(item)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        marker = QLabel()
        marker.setObjectName(f"legend_marker_{marker_type}")
        marker.setFixedSize(34, 14)
        marker.setToolTip(tooltip)
        label = PrimaryLabel(text)
        label.setToolTip(tooltip)
        layout.addWidget(marker)
        layout.addWidget(label)
        item.marker = marker
        item.label = label
        item.marker_type = marker_type
        item.legend_text = text
        self._theme_widgets.append(label)
        return item

    def _create_current_plot(self):
        plot = pg.PlotWidget()
        plot.setBackground(None)
        plot.setLabel("bottom", "Time (s)")
        plot.setLabel("left", "Current (mA)")
        plot_item = plot.getPlotItem()
        plot_item.getAxis("bottom").enableAutoSIPrefix(False)
        plot_item.getAxis("left").enableAutoSIPrefix(False)
        plot.showGrid(x=True, y=True, alpha=0.25)
        plot.setMouseEnabled(x=True, y=True)
        plot.setMenuEnabled(False)
        plot.setContextMenuPolicy(Qt.CustomContextMenu)

        colors = self._chart_colors()
        self.upper_sleep_limit_line = pg.InfiniteLine(
            pos=abs(self.current_limit_edit.value()),
            angle=0,
            movable=False,
            pen=pg.mkPen(colors["sleep"], width=1.5, style=Qt.DashLine),
        )
        self.lower_sleep_limit_line = pg.InfiniteLine(
            pos=-abs(self.current_limit_edit.value()),
            angle=0,
            movable=False,
            pen=pg.mkPen(colors["sleep"], width=1.5, style=Qt.DashLine),
        )
        self.upper_sleep_limit_line.setZValue(5)
        self.lower_sleep_limit_line.setZValue(5)
        plot.addItem(self.upper_sleep_limit_line)
        plot.addItem(self.lower_sleep_limit_line)

        self.current_curve = plot.plot(
            [],
            [],
            pen=pg.mkPen(colors["current"], width=2),
        )
        self.current_curve.setZValue(20)
        self.current_curve.setClipToView(True)
        self.current_curve.setDownsampling(auto=True, method="peak")

        self.hover_marker = pg.ScatterPlotItem(
            [],
            [],
            symbol="s",
            size=8,
            brush=pg.mkBrush(colors["hover_marker"]),
            pen=pg.mkPen(colors["hover_marker_border"], width=1),
        )
        self.hover_marker.setZValue(30)
        self.hover_marker.hide()
        plot.addItem(self.hover_marker)

        self.hover_label = pg.TextItem(anchor=(0, 1))
        self.hover_label.setZValue(40)
        self.hover_label.hide()
        plot.addItem(self.hover_label)

        self._mouse_move_proxy = pg.SignalProxy(
            plot.scene().sigMouseMoved,
            rateLimit=60,
            slot=self._update_hover_coordinates,
        )
        plot_item.vb.sigRangeChanged.connect(self.position_chart_pin_labels)
        return plot

    def _create_review_group(self):
        group = QGroupBox("Data Review")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 16, 12, 12)
        self.review_table = self._create_review_table()
        layout.addWidget(self.review_table, 1)
        return group

    def _create_right_panel(self):
        panel = QWidget()
        panel.setMinimumWidth(200)
        panel.setMaximumWidth(360)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.btn_run = PrimaryButton("RUN")
        self.btn_export = PrimaryButton("EXPORT")
        self.btn_copy_data_review = PrimaryButton("COPY Data Review")
        self.btn_copy_summary = PrimaryButton("COPY Summary")
        self.btn_clear = PrimaryButton("CLEAR")

        for button in (
            self.btn_run,
            self.btn_export,
            self.btn_copy_data_review,
            self.btn_copy_summary,
            self.btn_clear,
        ):
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            layout.addWidget(button)

        self.summary_widget = QCurrentSummaryWidget()
        self.summary_group = self.summary_widget
        layout.addWidget(self.summary_widget, 1)
        return panel

    def _create_placeholder_panel(self):
        label = QLabel(PLACEHOLDER_VALUE)
        label.setFrameShape(QFrame.StyledPanel)
        label.setAlignment(Qt.AlignCenter)
        label.setMinimumHeight(120)
        self._theme_widgets.append(label)
        return label

    def _create_review_table(self):
        table = QCurrentReviewTable()
        table.setObjectName("review_table")
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["No.", "Time", "Current (mA)"])
        table.setSortingEnabled(False)
        table.setRowCount(0)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        return table

    def browse_current_file(self):
        file_path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Select Current Data File",
            "",
            SOURCE_FILE_FILTER,
        )
        if not file_path:
            return

        self.set_source_file(file_path)

    def set_source_file(self, file_path: str | Path):
        path = Path(file_path).expanduser().resolve()
        path_text = str(path)
        self.source_file_edit.setText(path_text)
        self.source_file_edit.setToolTip(path_text)
        self.import_button.setEnabled(True)

    def _set_analysis_result(self, text):
        self.analysis_result_edit.setText(text)
        self._refresh_analysis_result_style()

    def _refresh_analysis_result_style(self):
        self.analysis_result_edit.fn_refresh_theme()
        state = self.analysis_result_edit.text().strip().upper()
        if state not in {"PASSED", "FAILED"}:
            return

        colors = ThemeManager.fn_colors()
        state_color = colors.SUCCESS if state == "PASSED" else colors.DANGER
        self.analysis_result_edit.setStyleSheet(
            self.analysis_result_edit.styleSheet()
            + f"""
            QLineEdit {{
                color: {state_color};
                font-weight: 700;
            }}
            """
        )

    def clear_source_file_selection(self):
        self.source_file_edit.clear()
        self.source_file_edit.setToolTip("")
        self.import_button.setEnabled(True)

    def import_current_file(self):
        source_text = self.source_file_edit.text().strip()
        if not source_text:
            self.load_selected_dataset()
            return

        source_path = Path(source_text).expanduser()
        try:
            source_path = source_path.resolve()
            normalized = normalize_current_data(source_path)
            dataset_name = default_dataset_name(source_path)
            database_path = database_path_for_source(source_path, self._database_dir)
        except Exception as error:
            self._set_analysis_result("IMPORT FAILED")
            QMessageBox.warning(self, "Q current Import", str(error))
            return

        if database_path.exists():
            response = QMessageBox.question(
                self,
                "Replace Dataset",
                (
                    f"Database '{database_path.name}' already exists.\n"
                    "Replace it with the selected file?"
                ),
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.No,
            )
            if response != QMessageBox.Yes:
                return

        try:
            result = import_dataset(
                dataset_name,
                source_path,
                normalized.rows,
                database_path,
                detected_channel=normalized.detected_channel,
            )
        except Exception as error:
            self._set_analysis_result("IMPORT FAILED")
            QMessageBox.warning(self, "Q current Import", str(error))
            return

        self.current_import = result
        self.current_database_path = result.dataset.database_path or database_path
        self.current_samples = get_samples(
            result.dataset.id,
            self.current_database_path,
        )
        self._load_samples_into_workspace(self.current_samples)
        self._refresh_dataset_combo(selected_db_path=self.current_database_path)
        self.clear_source_file_selection()
        self._set_analysis_result("IMPORTED")
        QMessageBox.information(
            self,
            "Q current Import",
            (
                f"Imported {result.row_count} rows.\n"
                f"Dataset: {result.dataset.name}\n"
                f"Channel: {result.dataset.detected_channel}\n"
                f"Database: {self.current_database_path}"
            ),
        )

    def load_selected_dataset(self):
        database_value = self.dataset_combo.currentData()
        if not database_value:
            QMessageBox.warning(
                self,
                "Q current Import",
                "Select an imported Q current dataset.",
            )
            return

        database_path = Path(database_value).expanduser().resolve()
        dataset = get_primary_dataset(database_path)
        if dataset is None:
            self._set_analysis_result("IMPORT FAILED")
            QMessageBox.warning(
                self,
                "Q current Import",
                f"Q current database is not valid: {database_path}",
            )
            return

        self.current_import = None
        self.current_database_path = dataset.database_path or database_path
        self.current_samples = get_samples(dataset.id, self.current_database_path)
        self._load_samples_into_workspace(self.current_samples)
        self._set_analysis_result("LOADED")
        self.import_button.setEnabled(True)

    def _load_samples_into_workspace(self, samples):
        self.current_samples = list(samples)
        self._chart_ready = False
        self._clear_current_chart()
        self.summary_widget.clear_result()
        self._populate_review_table(self.current_samples)
        self._update_action_states()

    def _update_action_states(self):
        has_data = bool(self.current_samples)
        has_chart = self._chart_ready
        has_analysis = self.current_analysis_result is not None
        self.btn_run.setEnabled(has_data)
        self.btn_copy_data_review.setEnabled(has_data)
        self.btn_clear.setEnabled(has_data)
        self.btn_export.setEnabled(has_analysis)
        self.btn_capture_chart.setEnabled(has_chart)
        self.btn_invert_y_axis.setEnabled(has_chart)
        self.btn_fit_all.setEnabled(has_chart)
        self.btn_copy_summary.setEnabled(has_analysis)

    def run_current_analysis(self):
        if not self.current_samples:
            self._update_action_states()
            return
        try:
            elapsed_seconds, current_values = self._build_chart_data()
            analysis_result = analyze_q_current(
                elapsed_seconds,
                current_values,
                self.current_limit_edit.value(),
                self.wake_limit_edit.value(),
                self.wake_duration_edit.value(),
                source_times=[sample.time for sample in self.current_samples],
            )
        except ValueError as error:
            QMessageBox.warning(self, "Q current Chart", str(error))
            self._update_action_states()
            return

        self._update_current_chart(
            elapsed_seconds,
            current_values,
            analysis_result.wake_up_intervals,
        )
        self.summary_widget.set_result(analysis_result)
        self.current_analysis_result = analysis_result
        self.current_analysis_settings = QCurrentReportSettings(
            standard_current_ma=self.current_limit_edit.value(),
            wake_up_limit_ma=self.wake_limit_edit.value(),
            wake_duration_s=self.wake_duration_edit.value(),
        )
        self._chart_ready = True
        self._set_analysis_result(analysis_result.result_status)
        self._update_action_states()

    def clear_current_workspace(self):
        self.current_import = None
        self.current_database_path = None
        self.current_samples = []
        self.current_analysis_result = None
        self.current_analysis_settings = None
        self._chart_ready = False
        self.review_table.setRowCount(0)
        self._clear_current_chart()
        self.summary_widget.clear_result()
        self._set_analysis_result("NOT RUN")
        self._update_action_states()

    def _build_chart_data(self):
        elapsed_seconds = calculate_elapsed_seconds(self.current_samples)
        if not elapsed_seconds:
            raise ValueError("Q current data contains no valid timestamps.")
        current_values = [float(sample.current_mA) for sample in self.current_samples]
        if len(elapsed_seconds) != len(current_values):
            raise ValueError("Q current chart data is not aligned.")
        return elapsed_seconds, current_values

    def _update_current_chart(self, elapsed_seconds, current_values, wake_up_intervals):
        self.clear_chart_pins()
        time_array = np.asarray(elapsed_seconds, dtype=float)
        current_array = np.asarray(current_values, dtype=float)
        if time_array.size != current_array.size:
            raise ValueError("Q current chart data is not aligned.")
        order = np.argsort(time_array)
        time_array = time_array[order]
        current_array = current_array[order]
        self.chart_time_seconds = time_array
        self.chart_current_ma = current_array

        x_min = float(time_array[0])
        x_max = float(time_array[-1]) if time_array.size > 1 else x_min + 1.0
        self.current_curve.setData(time_array, current_array)
        self.update_sleep_limit_lines(
            self.current_limit_edit.value(),
            mark_not_run=False,
        )
        self.update_wake_up_regions(wake_up_intervals)
        self.hide_hover_items()
        self._update_chart_scrollbar(x_min, x_max)
        self._fit_all_current_chart()

        self.chart_placeholder.hide()
        self.current_plot.show()

    def _fit_all_current_chart(self):
        if self.chart_time_seconds.size == 0:
            return

        x_min = float(self.chart_time_seconds[0])
        x_max = float(self.chart_time_seconds[-1])

        if x_max <= x_min:
            x_max = x_min + 1.0

        self.current_plot.setXRange(
            x_min,
            x_max,
            padding=0.02,
        )

        y_min = float(np.min(self.chart_current_ma))
        y_max = float(np.max(self.chart_current_ma))
        if y_max <= y_min:
            y_min -= 1.0
            y_max += 1.0
        self.current_plot.setYRange(y_min, y_max, padding=0.08)
        self.position_chart_pin_labels()

    def _update_chart_scrollbar(self, x_min, x_max):
        self._chart_x_min = float(x_min)
        self._chart_x_max = float(x_max)
        total_span = max(0.0, self._chart_x_max - self._chart_x_min)
        self._chart_visible_span = min(
            CHART_SCROLL_VISIBLE_SECONDS,
            total_span if total_span > 0.0 else CHART_SCROLL_VISIBLE_SECONDS,
        )
        max_scroll = max(
            0,
            int(round((total_span - self._chart_visible_span) * CHART_SCROLL_SCALE)),
        )

        self._chart_scrollbar_updating = True
        self.chart_scrollbar.setRange(0, max_scroll)
        self.chart_scrollbar.setPageStep(
            max(1, int(round(self._chart_visible_span * CHART_SCROLL_SCALE)))
        )
        self.chart_scrollbar.setSingleStep(CHART_SCROLL_SCALE)
        self.chart_scrollbar.setValue(0)
        self.chart_scrollbar.setVisible(max_scroll > 0)
        self._chart_scrollbar_updating = False

        self._apply_chart_scrollbar_range()

    def _on_chart_scrollbar_changed(self, _value=None):
        if self._chart_scrollbar_updating or not self._chart_ready:
            return
        self._apply_chart_scrollbar_range()

    def _apply_chart_scrollbar_range(self):
        total_span = max(0.0, self._chart_x_max - self._chart_x_min)
        if total_span <= 0.0:
            self.current_plot.setXRange(
                self._chart_x_min,
                self._chart_x_min + 1.0,
                padding=0.02,
            )
            self.position_chart_pin_labels()
            return

        if self.chart_scrollbar.maximum() <= 0:
            self.current_plot.setXRange(
                self._chart_x_min,
                self._chart_x_max,
                padding=0.02,
            )
            self.position_chart_pin_labels()
            return

        start = (
            self._chart_x_min
            + self.chart_scrollbar.value() / CHART_SCROLL_SCALE
        )
        end = min(start + self._chart_visible_span, self._chart_x_max)
        if end <= start:
            end = start + 1.0
        self.current_plot.setXRange(start, end, padding=0)
        self.position_chart_pin_labels()

    def toggle_y_axis_inversion(self):
        self._y_axis_inverted = not self._y_axis_inverted
        self._apply_y_axis_orientation()

    def reset_y_axis_orientation(self):
        self._y_axis_inverted = False
        if hasattr(self, "current_plot"):
            self._apply_y_axis_orientation()

    def _apply_y_axis_orientation(self):
        view_box = self.current_plot.getPlotItem().getViewBox()
        view_box.invertY(self._y_axis_inverted)
        self.position_chart_pin_labels()

    def save_current_config(self):
        config = QCurrentConfig(
            standard_current_ma=self.current_limit_edit.value(),
            wake_up_limit_ma=self.wake_limit_edit.value(),
            wake_duration_s=self.wake_duration_edit.value(),
        )
        try:
            save_q_current_config(config, self._config_file)
        except Exception as error:
            QMessageBox.critical(self, "Save Config Error", str(error))
            return False
        self.q_current_config = config
        QMessageBox.information(
            self,
            "Save Config",
            "Q Current configuration saved successfully.",
        )
        return True
    def capture_current_chart(self):
        if not self._chart_ready:
            return False
        pixmap = self.current_plot.grab()
        if pixmap.isNull():
            return False
        QApplication.clipboard().setPixmap(pixmap)
        return True

    def export_q_current_report(self):
        if self.current_analysis_result is None or self.current_analysis_settings is None:
            return None
        report_data = QCurrentReportData(
            dataset_name=self.dataset_combo.currentText(),
            samples=list(self.current_samples),
            analysis_result=self.current_analysis_result,
            settings=self.current_analysis_settings,
            chart_png=self._grab_current_chart_png(),
        )
        try:
            output_file = self.q_current_report_service.fn_export(self, report_data)
        except Exception as error:
            QMessageBox.critical(self, "Export Error", str(error))
            return None
        if output_file is not None:
            QMessageBox.information(
                self,
                "Export",
                f"Excel report saved:\n\n{output_file}",
            )
        return output_file

    def _grab_current_chart_png(self):
        if not self._chart_ready:
            return None
        pixmap = self.current_plot.grab()
        if pixmap.isNull():
            return None
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        if not buffer.open(QIODevice.WriteOnly):
            return None
        if not pixmap.save(buffer, "PNG"):
            buffer.close()
            return None
        buffer.close()
        return bytes(byte_array)

    def update_sleep_limit_lines(self, limit_ma, mark_not_run=True):
        if self.upper_sleep_limit_line is None or self.lower_sleep_limit_line is None:
            return
        limit_ma = abs(float(limit_ma))
        self.upper_sleep_limit_line.setValue(limit_ma)
        self.lower_sleep_limit_line.setValue(-limit_ma)
        self._update_sleep_legend_tooltip(limit_ma)
        if mark_not_run:
            self._mark_analysis_not_run()

    def _update_sleep_legend_tooltip(self, limit_ma):
        tooltip = f"Sleep band: -{limit_ma:.1f} mA to +{limit_ma:.1f} mA"
        for item in getattr(self, "legend_items", []):
            if item.legend_text == "Sleep threshold":
                item.setToolTip(tooltip)
                item.marker.setToolTip(tooltip)
                item.label.setToolTip(tooltip)
                break

    def _mark_analysis_not_run(self, *_args):
        self.current_analysis_result = None
        self.current_analysis_settings = None
        if hasattr(self, "analysis_result_edit"):
            self._set_analysis_result("NOT RUN")
        if hasattr(self, "summary_widget"):
            self.summary_widget.clear_result()
        if hasattr(self, "btn_export"):
            self._update_action_states()

    def create_wake_up_region(self, start_s, end_s):
        region = pg.LinearRegionItem(
            values=(float(start_s), float(end_s)),
            orientation="vertical",
            movable=False,
            brush=self._transparent_brush(
                self._chart_colors()["wake_fill"],
                70,
            ),
        )
        region.setZValue(-10)
        for line in getattr(region, "lines", []):
            line.setPen(pg.mkPen(None))
            line.setHoverPen(pg.mkPen(None))
            line.setMovable(False)
        return region

    def update_wake_up_regions(self, intervals):
        self.clear_wake_up_regions()
        for interval in intervals:
            region = self.create_wake_up_region(
                interval.start_s,
                interval.end_s,
            )
            self.wake_up_regions.append(region)
            self.current_plot.addItem(region)

    def clear_wake_up_regions(self):
        if not hasattr(self, "current_plot"):
            return
        for region in self.wake_up_regions:
            self.current_plot.removeItem(region)
        self.wake_up_regions = []

    def find_nearest_sample(self, mouse_time_s):
        nearest_index = self.find_nearest_sample_index(mouse_time_s)
        if nearest_index is None:
            return None
        return (
            float(self.chart_time_seconds[nearest_index]),
            float(self.chart_current_ma[nearest_index]),
        )

    def show_chart_context_menu(self, widget_position):
        scene_position = self.current_plot.mapToScene(widget_position)
        action_type, payload = self._chart_context_action_at_scene_position(
            scene_position
        )
        if action_type is None:
            return

        menu, primary_action, clear_action = self._create_chart_context_menu(
            action_type
        )
        selected_action = menu.exec(self.current_plot.mapToGlobal(widget_position))
        self._apply_chart_context_menu_selection(
            selected_action,
            primary_action,
            clear_action,
            action_type,
            payload,
        )

    def _create_chart_context_menu(self, action_type):
        menu = QMenu(self.current_plot)
        if action_type == "delete":
            primary_action = menu.addAction("Delete Pin")
        else:
            primary_action = menu.addAction("Pin")

        clear_action = None
        if self.chart_pins:
            menu.addSeparator()
            clear_action = menu.addAction("Clear All Pins")
        return menu, primary_action, clear_action

    def _apply_chart_context_menu_selection(
        self,
        selected_action,
        primary_action,
        clear_action,
        action_type,
        payload,
    ):
        if selected_action is None:
            return
        if clear_action is not None and selected_action is clear_action:
            self.clear_chart_pins()
            return
        if selected_action is not primary_action:
            return
        if action_type == "delete":
            self.delete_chart_pin(payload)
        elif action_type == "pin":
            self.pin_chart_sample(payload)

    def _chart_context_action_at_scene_position(self, scene_position):
        if (
            scene_position is None
            or not self._chart_ready
            or self.chart_time_seconds.size == 0
        ):
            return None, None

        plot_item = self.current_plot.getPlotItem()
        if not plot_item.sceneBoundingRect().contains(scene_position):
            return None, None

        pin = self._chart_pin_at_scene_position(scene_position)
        if pin is not None:
            return "delete", pin

        sample_index = self._chart_sample_at_scene_position(scene_position)
        if sample_index is None:
            return None, None

        pin = self._pin_for_sample_index(sample_index)
        if pin is not None:
            return "delete", pin
        return "pin", sample_index

    def _chart_pin_at_scene_position(self, scene_position):
        closest_pin = None
        closest_distance = PIN_HIT_RADIUS_PX
        for pin in self.chart_pins:
            pin_scene_position = self._scene_position_for_chart_value(
                pin.time_s,
                pin.current_ma,
            )
            distance = self._scene_distance(scene_position, pin_scene_position)
            if distance <= closest_distance:
                closest_pin = pin
                closest_distance = distance
        return closest_pin

    def _chart_sample_at_scene_position(self, scene_position):
        point = self.current_plot.getPlotItem().vb.mapSceneToView(scene_position)
        sample_index = self.find_nearest_sample_index(point.x())
        if sample_index is None:
            return None
        sample_scene_position = self._scene_position_for_chart_sample(sample_index)
        distance = self._scene_distance(scene_position, sample_scene_position)
        if distance > SAMPLE_HIT_RADIUS_PX:
            return None
        return sample_index

    def _scene_position_for_chart_sample(self, sample_index):
        return self._scene_position_for_chart_value(
            float(self.chart_time_seconds[sample_index]),
            float(self.chart_current_ma[sample_index]),
        )

    def _scene_position_for_chart_value(self, time_s, current_ma):
        view_box = self.current_plot.getPlotItem().getViewBox()
        return view_box.mapViewToScene(pg.Point(float(time_s), float(current_ma)))

    @staticmethod
    def _scene_distance(first_position, second_position):
        dx = first_position.x() - second_position.x()
        dy = first_position.y() - second_position.y()
        return (dx * dx + dy * dy) ** 0.5

    def pin_chart_sample(self, sample_index):
        if sample_index is None:
            return False
        sample_index = int(sample_index)
        if sample_index < 0 or sample_index >= self.chart_time_seconds.size:
            return False
        if self._pin_for_sample_index(sample_index) is not None:
            return False

        time_s = float(self.chart_time_seconds[sample_index])
        current_ma = float(self.chart_current_ma[sample_index])
        colors = self._chart_colors()
        marker = pg.ScatterPlotItem(
            [time_s],
            [current_ma],
            symbol="o",
            size=10,
            brush=pg.mkBrush(colors["pin_marker"]),
            pen=pg.mkPen(colors["pin_marker_border"], width=1.5),
        )
        marker.setZValue(35)
        label = pg.TextItem(anchor=(0, 1))
        label.setZValue(45)
        label.setHtml(self._pin_label_html(time_s, current_ma))
        pin = ChartPin(
            sample_index=sample_index,
            time_s=time_s,
            current_ma=current_ma,
            marker=marker,
            label=label,
        )
        self.current_plot.addItem(marker)
        self.current_plot.addItem(label)
        self.chart_pins.append(pin)
        self.position_chart_pin_label(pin)
        return True

    def delete_chart_pin(self, pin):
        if pin not in self.chart_pins:
            return False
        self.current_plot.removeItem(pin.marker)
        self.current_plot.removeItem(pin.label)
        self.chart_pins.remove(pin)
        return True

    def clear_chart_pins(self):
        if not hasattr(self, "current_plot"):
            self.chart_pins = []
            return
        for pin in list(self.chart_pins):
            self.current_plot.removeItem(pin.marker)
            self.current_plot.removeItem(pin.label)
        self.chart_pins = []

    def _pin_for_sample_index(self, sample_index):
        for pin in self.chart_pins:
            if pin.sample_index == sample_index:
                return pin
        return None

    def position_chart_pin_labels(self, *_args):
        for pin in self.chart_pins:
            self.position_chart_pin_label(pin)

    def position_chart_pin_label(self, pin):
        x_range, y_range = self.current_plot.getPlotItem().viewRange()
        x_mid = (x_range[0] + x_range[1]) / 2.0
        y_mid = (y_range[0] + y_range[1]) / 2.0
        anchor_x = 0 if pin.time_s <= x_mid else 1
        anchor_y = 1 if pin.current_ma >= y_mid else 0
        x_offset = (0.02 if anchor_x == 0 else -0.02) * (x_range[1] - x_range[0])
        y_offset = (0.04 if anchor_y == 0 else -0.04) * (y_range[1] - y_range[0])
        pin.label.setAnchor((anchor_x, anchor_y))
        pin.label.setPos(pin.time_s + x_offset, pin.current_ma + y_offset)

    def _pin_label_html(self, time_s, current_ma):
        colors = self._chart_colors()
        return (
            f"<div style='background-color: {colors['pin_label_background']}; "
            f"color: {colors['pin_label_text']}; padding: 4px; "
            "white-space: nowrap;'>"
            f"Time: {time_s:.3f} s<br/>"
            f"Current: {current_ma:.2f} mA"
            "</div>"
        )

    def _refresh_chart_pin_theme(self):
        colors = self._chart_colors()
        for pin in self.chart_pins:
            pin.marker.setBrush(pg.mkBrush(colors["pin_marker"]))
            pin.marker.setPen(pg.mkPen(colors["pin_marker_border"], width=1.5))
            pin.label.setHtml(self._pin_label_html(pin.time_s, pin.current_ma))
            self.position_chart_pin_label(pin)

    def find_nearest_sample_index(self, mouse_time_s):
        if self.chart_time_seconds.size == 0:
            return None
        index = int(np.searchsorted(self.chart_time_seconds, mouse_time_s))
        candidates = []
        if index < self.chart_time_seconds.size:
            candidates.append(index)
        if index > 0:
            candidates.append(index - 1)
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda candidate: abs(
                self.chart_time_seconds[candidate] - mouse_time_s
            ),
        )

    def update_hover_items(self, time_s, current_ma):
        self._hover_sample = (float(time_s), float(current_ma))
        self.hover_marker.setData([time_s], [current_ma])
        self.hover_marker.show()
        self.hover_label.setHtml(self._hover_label_html(time_s, current_ma))
        self.position_hover_label(time_s, current_ma)
        self.hover_label.show()
     
    def position_hover_label(self, time_s, current_ma):
        x_range, y_range = self.current_plot.getPlotItem().viewRange()
        x_mid = (x_range[0] + x_range[1]) / 2.0
        y_mid = (y_range[0] + y_range[1]) / 2.0
        anchor_x = 1 if time_s >= x_mid else 0
        anchor_y = 0 if current_ma >= y_mid else 1
        x_offset = (-0.02 if anchor_x else 0.02) * (x_range[1] - x_range[0])
        y_offset = (-0.04 if anchor_y == 0 else 0.04) * (y_range[1] - y_range[0])
        self.hover_label.setAnchor((anchor_x, anchor_y))
        self.hover_label.setPos(time_s + x_offset, current_ma + y_offset)

    def hide_hover_items(self):
        if self.hover_marker is not None:
            self.hover_marker.hide()
        if self.hover_label is not None:
            self.hover_label.hide()
        self._hover_sample = None
        
    def _hover_label_html(self, time_s, current_ma):
        colors = self._chart_colors()
        return (
            f"<div style='background-color: {colors['hover_label_background']}; "
            f"color: {colors['hover_label_text']}; padding: 4px; "
            "white-space: nowrap;'>"
            f"Time: {time_s:.3f} s<br/>"
            f"Current: {current_ma:.2f} mA"
            "</div>"
        )

    def _clear_current_chart(self):
        if not hasattr(self, "current_plot"):
            return
        self.current_curve.setData([], [])
        self.reset_y_axis_orientation()
        self.clear_chart_pins()
        self.clear_wake_up_regions()
        self.chart_time_seconds = np.array([], dtype=float)
        self.chart_current_ma = np.array([], dtype=float)
        self.hide_hover_items()
        self._chart_scrollbar_updating = True
        self.chart_scrollbar.setValue(self.chart_scrollbar.minimum())
        self.chart_scrollbar.hide()
        self._chart_scrollbar_updating = False
        self.current_plot.getPlotItem().enableAutoRange()
        self.current_plot.hide()
        self.chart_placeholder.show()

    def _update_hover_coordinates(self, event):
        if not self._chart_ready or self.chart_time_seconds.size == 0:
            self.hide_hover_items()
            return
        position = event[0]
        plot_item = self.current_plot.getPlotItem()
        if not plot_item.sceneBoundingRect().contains(position):
            self.hide_hover_items()
            return
        point = plot_item.vb.mapSceneToView(position)
        nearest_sample = self.find_nearest_sample(point.x())
        if nearest_sample is None:
            self.hide_hover_items()
            return
        self.update_hover_items(*nearest_sample)

    def _chart_colors(self):
        colors = ThemeManager.fn_colors()
        return {
            "current": colors.PRIMARY,
            "sleep": colors.WARNING,
            "wake": colors.WARNING,
            "wake_fill": colors.WARNING,
            "hover_marker": colors.PRIMARY,
            "hover_marker_border": colors.TEXT,
            "hover_label_background": colors.WINDOW,
            "hover_label_text": colors.TEXT,
            "pin_marker": colors.SUCCESS,
            "pin_marker_border": colors.TEXT,
            "pin_label_background": colors.WINDOW,
            "pin_label_text": colors.TEXT,
            "background": colors.WINDOW,
            "grid": colors.TABLE_GRID,
            "axis": colors.TEXT,
        }

    def _refresh_chart_theme(self):
        if not hasattr(self, "current_plot"):
            return
        chart_colors = self._chart_colors()
        self.current_plot.setBackground(chart_colors["background"])
        plot_item = self.current_plot.getPlotItem()
        plot_item.getAxis("bottom").setPen(chart_colors["axis"])
        plot_item.getAxis("bottom").setTextPen(chart_colors["axis"])
        plot_item.getAxis("left").setPen(chart_colors["axis"])
        plot_item.getAxis("left").setTextPen(chart_colors["axis"])
        self.chart_scrollbar.setStyleSheet(fn_scrollbar_style())
        self.current_curve.setPen(pg.mkPen(chart_colors["current"], width=2))
        sleep_pen = pg.mkPen(
            chart_colors["sleep"],
            width=1.5,
            style=Qt.DashLine,
        )
        self.upper_sleep_limit_line.setPen(sleep_pen)
        self.lower_sleep_limit_line.setPen(sleep_pen)
        wake_brush = self._transparent_brush(chart_colors["wake_fill"], 70)
        for region in self.wake_up_regions:
            region.setBrush(wake_brush)
            for line in getattr(region, "lines", []):
                line.setPen(pg.mkPen(None))
                line.setHoverPen(pg.mkPen(None))
        self.hover_marker.setBrush(pg.mkBrush(chart_colors["hover_marker"]))
        self.hover_marker.setPen(
            pg.mkPen(chart_colors["hover_marker_border"], width=1)
        )
        self._refresh_visible_hover_label()
        self._refresh_chart_pin_theme()
        self._refresh_legend_theme()

    def _transparent_brush(self, color_value, alpha):
        color = QColor(color_value)
        color.setAlpha(alpha)
        return pg.mkBrush(color)

    def _refresh_visible_hover_label(self):
        if self.hover_label is None or not self.hover_label.isVisible():
            return
        if self._hover_sample is not None:
            self.hover_label.setHtml(self._hover_label_html(*self._hover_sample))

    def _refresh_legend_theme(self):
        if not hasattr(self, "legend_items"):
            return
        chart_colors = self._chart_colors()
        marker_styles = {
            "line-solid": (
                f"border-top: 3px solid {chart_colors['current']};"
                "background: transparent;"
            ),
            "line-dashed": (
                f"border-top: 3px dashed {chart_colors['sleep']};"
                "background: transparent;"
            ),
            "dot": (
                f"background: {chart_colors['wake']};"
                "border-radius: 6px;"
                "max-width: 12px; min-width: 12px;"
                "max-height: 12px; min-height: 12px;"
            ),
        }
        for item in self.legend_items:
            item.marker.setStyleSheet(marker_styles[item.marker_type])
        

    def _populate_review_table(self, samples):
        self.review_table.setSortingEnabled(False)
        self.review_table.setRowCount(0)
        for row, sample in enumerate(samples):
            self.review_table.insertRow(row)
            self.review_table.setItem(
                row,
                0,
                self.review_table.fn_create_item(
                    row + 1,
                    row,
                    Qt.AlignCenter,
                ),
            )
            self.review_table.setItem(
                row,
                1,
                self.review_table.fn_create_item(sample.time, row),
            )
            self.review_table.setItem(
                row,
                2,
                self.review_table.fn_create_item(
                    f"{sample.current_mA:.2f}",
                    row,
                    Qt.AlignRight | Qt.AlignVCenter,
                ),
            )

        self.review_table.scrollToTop()
        self.review_table.verticalScrollBar().setValue(
            self.review_table.verticalScrollBar().minimum()
        )
        self.review_table.horizontalScrollBar().setValue(
            self.review_table.horizontalScrollBar().minimum()
        )

    def copy_data_review(self):
        QApplication.clipboard().setText(self._review_table_to_text())

    def copy_summary(self):
        QApplication.clipboard().setText(self.summary_widget.to_text())

    def _review_table_to_text(self):
        headers = [
            self.review_table.horizontalHeaderItem(column).text()
            for column in range(self.review_table.columnCount())
        ]
        rows = ["\t".join(headers)]
        for row in range(self.review_table.rowCount()):
            values = []
            for column in range(self.review_table.columnCount()):
                item = self.review_table.item(row, column)
                values.append(item.text() if item is not None else "")
            rows.append("\t".join(values))
        return "\n".join(rows)

    def _summary_to_text(self):
        return self.summary_widget.to_text()

    def _refresh_dataset_combo(self, selected_db_path: Path | str | None = None):
        selected_path = selected_db_path
        if selected_path is None:
            selected_path = self.dataset_combo.currentData()
        if selected_path is not None:
            selected_path = str(Path(selected_path).expanduser().resolve())

        self.dataset_combo.clear()
        for dataset in list_datasets(self._database_dir):
            if dataset.database_path is None:
                continue
            db_path = dataset.database_path.resolve()
            self.dataset_combo.addItem(
                db_path.stem,
                str(db_path),
            )

        if selected_path is not None:
            index = self.dataset_combo.findData(selected_path)
            if index >= 0:
                self.dataset_combo.setCurrentIndex(index)

    @staticmethod
    def _is_valid_source_file(path: Path) -> bool:
        return (
            path.exists()
            and path.is_file()
            and path.suffix.lower() in SUPPORTED_SOURCE_EXTENSIONS
        )

    def fn_refresh_theme(self):
        group_style = fn_groupbox_style()
        for group in (
            self.settings_group,
            self.chart_group,
            self.review_group,
            self.summary_group,
        ):
            group.setStyleSheet(group_style)

        for widget in (
            self.source_file_edit,
            self.analysis_result_edit,
            self.dataset_combo,
            self.review_table,
            self.browse_button,
            self.import_button,
            self.save_config_button,
            self.btn_run,
            self.btn_export,
            self.btn_invert_y_axis,
            self.btn_fit_all,
            self.btn_capture_chart,
            self.btn_copy_data_review,
            self.btn_copy_summary,
            self.btn_clear,
        ):
            widget.fn_refresh_theme()

        spinbox_style = fn_spinbox_style()
        for spinbox in (
            self.current_limit_edit,
            self.wake_limit_edit,
            self.wake_duration_edit,
        ):
            spinbox.setStyleSheet(spinbox_style)

        for label in self.findChildren(PrimaryLabel):
            label.fn_refresh_theme()

        self.summary_widget.fn_refresh_theme()
        self._refresh_analysis_result_style()
        self._refresh_chart_theme()

        colors = ThemeManager.fn_colors()
        value_style = f"""
            QLabel {{
                color: {colors.TEXT};
                background: transparent;
                font-size: 10pt;
            }}
        """
        placeholder_style = f"""
            QLabel {{
                color: {colors.TEXT};
                background: {colors.WINDOW};
                border: 1px solid {colors.BORDER};
                border-radius: 6px;
                font-size: 18pt;
                font-weight: 600;
            }}
        """
        for label in self._theme_widgets:
            if label is self.chart_placeholder:
                label.setStyleSheet(placeholder_style)
            else:
                label.setStyleSheet(value_style)
