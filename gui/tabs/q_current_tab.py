from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QHeaderView,
)

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
from gui.themes.styles.controls.scrollbar_style import fn_apply_scrollbar_style
from gui.themes.styles.controls.spinbox_style import fn_spinbox_style
from gui.themes.theme_manager import ThemeManager
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_combobox import PrimaryComboBox
from gui.widgets.controls.primary_label import PrimaryLabel
from gui.widgets.controls.primary_lineedit import PrimaryLineEdit
from gui.widgets.controls.primary_table import PrimaryTable


PLACEHOLDER_VALUE = "\u2014"
SOURCE_FILE_PLACEHOLDER = "Select current data file (*.csv, *.xlsx)"
SUPPORTED_SOURCE_EXTENSIONS = {".csv", ".xlsx"}
SOURCE_FILE_FILTER = (
    "Supported Files (*.csv *.xlsx);;"
    "CSV Files (*.csv);;"
    "Excel Files (*.xlsx)"
)
TIMESTAMP_FORMATS = (
    "%y-%m-%d %H:%M:%S.%f",
    "%y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
)


def parse_timestamp(value):
    text = str(value).strip()
    if not text:
        raise ValueError("empty timestamp")
    try:
        return float(text)
    except ValueError:
        pass
    for timestamp_format in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(text, timestamp_format)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text)
    except ValueError as error:
        raise ValueError(f"Unsupported timestamp: {text}") from error


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

    def __init__(self, database_dir: str | Path | None = None):
        super().__init__()

        self._theme_widgets = []
        self._database_dir = database_dir
        self.current_import = None
        self.current_samples = []
        self.current_database_path = None
        self._chart_ready = False
        self.current_curve = None
        self.sleep_threshold_curve = None
        self.wake_threshold_curve = None
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
        self.btn_clear.clicked.connect(self.clear_current_workspace)
        self.btn_copy_data_review.clicked.connect(self.copy_data_review)
        self.btn_copy_summary.clicked.connect(self.copy_summary)

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
        self.current_limit_edit.setValue(30.0)
        self.current_limit_edit.setFixedWidth(110)
        self.current_limit_edit.setMinimumHeight(36)
        self.current_limit_edit.lineEdit().setAlignment(Qt.AlignCenter)

        self.sleep_duration_label = PrimaryLabel(
            "Sleep duration (s)"
        )

        self.sleep_duration_edit = QDoubleSpinBox()
        self.sleep_duration_edit.setObjectName("sleep_duration_edit")
        self.sleep_duration_edit.setDecimals(1)
        self.sleep_duration_edit.setMinimum(10)
        self.sleep_duration_edit.setMaximum(1000000.0)
        self.sleep_duration_edit.setSingleStep(1)
        self.sleep_duration_edit.setValue(60)
        self.sleep_duration_edit.setFixedWidth(110)
        self.sleep_duration_edit.setMinimumHeight(36)
        self.sleep_duration_edit.lineEdit().setAlignment(Qt.AlignCenter)

        self.wake_limit_label = PrimaryLabel(
            "Wake Up limit (mA)"
        )

        self.wake_limit_edit = QDoubleSpinBox()
        self.wake_limit_edit.setObjectName("wake_limit_edit")
        self.wake_limit_edit.setDecimals(1)
        self.wake_limit_edit.setMinimum(0.0)
        self.wake_limit_edit.setMaximum(1000000.0)
        self.wake_limit_edit.setSingleStep(0.5)
        self.wake_limit_edit.setValue(300.0)
        self.wake_limit_edit.setFixedWidth(110)
        self.wake_limit_edit.setMinimumHeight(36)
        self.wake_limit_edit.lineEdit().setAlignment(Qt.AlignCenter)

        self.wake_duration_label = PrimaryLabel(
            "Wake duration (s)"
        )

        self.wake_duration_edit = QDoubleSpinBox()
        self.wake_duration_edit.setObjectName("wake_duration_edit")
        self.wake_duration_edit.setDecimals(1)
        self.wake_duration_edit.setMinimum(1.0)
        self.wake_duration_edit.setMaximum(3600.0)
        self.wake_duration_edit.setSingleStep(0.5)
        self.wake_duration_edit.setValue(2.0)
        self.wake_duration_edit.setFixedWidth(110)
        self.wake_duration_edit.setMinimumHeight(36)
        self.wake_duration_edit.lineEdit().setAlignment(Qt.AlignCenter)

        self.analysis_result_label = PrimaryLabel(
            "Analysis result:"
        )

        self.analysis_result_edit = PrimaryLineEdit()
        self.analysis_result_edit.setObjectName(
            "analysis_result_edit"
        )
        self.analysis_result_edit.setReadOnly(True)
        self.analysis_result_edit.setText("NOT RUN")
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
        result_layout.addWidget(self.sleep_duration_label)
        result_layout.addWidget(self.sleep_duration_edit)
        result_layout.addSpacing(16)

        result_layout.addWidget(self.wake_limit_label)
        result_layout.addWidget(self.wake_limit_edit)
        result_layout.addSpacing(16)
        result_layout.addWidget(self.wake_duration_label)
        result_layout.addWidget(self.wake_duration_edit)
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
        self.chart_placeholder = self._create_placeholder_panel()
        self.current_plot = self._create_current_plot()
        self.current_plot.hide()
        self.chart_layout.addWidget(self.chart_placeholder, 1)
        self.chart_layout.addWidget(self.current_plot, 1)
        return group

    def _create_current_plot(self):
        plot = pg.PlotWidget()
        plot.setBackground(None)
        plot.setLabel("bottom", "Time", units="s")
        plot.setLabel("left", "Current", units="mA")
        plot.showGrid(x=True, y=True, alpha=0.25)
        plot.addLegend()
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
        panel.setMaximumWidth(280)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.btn_run = PrimaryButton("RUN")
        self.btn_export = PrimaryButton("EXPORT")
        self.btn_copy_chart = PrimaryButton("COPY CHART")
        self.btn_copy_data_review = PrimaryButton("COPY Data Review")
        self.btn_copy_summary = PrimaryButton("COPY Summary")
        self.btn_clear = PrimaryButton("CLEAR")

        for button in (
            self.btn_run,
            self.btn_export,
            self.btn_copy_chart,
            self.btn_copy_data_review,
            self.btn_copy_summary,
            self.btn_clear,
        ):
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            layout.addWidget(button)

        self.summary_group = self._create_summary_group()
        layout.addWidget(self.summary_group, 1)
        return panel

    def _create_summary_group(self):
        group = QGroupBox("Summary")
        layout = QGridLayout(group)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(8)

        self.summary_labels = {}
        self.summary_values = {}
        rows = (
            ("sample_count", "Samples"),
            ("duration", "Duration"),
            ("min_current", "Min Current"),
            ("max_current", "Max Current"),
            ("avg_current", "Average Current"),
        )
        for row, (key, label_text) in enumerate(rows):
            label = PrimaryLabel(label_text)
            self.summary_labels[key] = label
            layout.addWidget(label, row, 0)
            value_label = self._create_value_label()
            self.summary_values[key] = value_label
            layout.addWidget(value_label, row, 1)

        layout.setColumnStretch(1, 1)
        layout.setRowStretch(len(rows), 1)
        return group

    def _create_value_label(self):
        label = PrimaryLabel(PLACEHOLDER_VALUE)
        label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self._theme_widgets.append(label)
        return label

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
            self.analysis_result_edit.setText("IMPORT FAILED")
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
            self.analysis_result_edit.setText("IMPORT FAILED")
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
        self.analysis_result_edit.setText("IMPORTED")
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
            self.analysis_result_edit.setText("IMPORT FAILED")
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
        self.analysis_result_edit.setText("LOADED")
        self.import_button.setEnabled(True)

    def _load_samples_into_workspace(self, samples):
        self.current_samples = list(samples)
        self._chart_ready = False
        self._clear_current_chart()
        self._populate_review_table(self.current_samples)
        self._update_action_states()

    def _update_action_states(self):
        has_data = bool(self.current_samples)
        has_chart = self._chart_ready
        self.btn_run.setEnabled(has_data)
        self.btn_copy_data_review.setEnabled(has_data)
        self.btn_clear.setEnabled(has_data)
        self.btn_export.setEnabled(has_chart)
        self.btn_copy_chart.setEnabled(has_chart)
        self.btn_copy_summary.setEnabled(has_chart)

    def run_current_analysis(self):
        if not self.current_samples:
            self._update_action_states()
            return
        try:
            elapsed_seconds, current_values = self._build_chart_data()
        except ValueError as error:
            QMessageBox.warning(self, "Q current Chart", str(error))
            self._update_action_states()
            return

        self._update_current_chart(elapsed_seconds, current_values)
        self._chart_ready = True
        self._update_action_states()

    def clear_current_workspace(self):
        self.current_import = None
        self.current_database_path = None
        self.current_samples = []
        self._chart_ready = False
        self.review_table.setRowCount(0)
        self._clear_current_chart()
        self.analysis_result_edit.setText("NOT RUN")
        self._update_action_states()

    def _build_chart_data(self):
        elapsed_seconds = calculate_elapsed_seconds(self.current_samples)
        if not elapsed_seconds:
            raise ValueError("Q current data contains no valid timestamps.")
        current_values = [float(sample.current_mA) for sample in self.current_samples]
        if len(elapsed_seconds) != len(current_values):
            raise ValueError("Q current chart data is not aligned.")
        return elapsed_seconds, current_values

    def _update_current_chart(self, elapsed_seconds, current_values):
        plot_item = self.current_plot.getPlotItem()
        plot_item.clear()
        if plot_item.legend is None:
            plot_item.addLegend()
        else:
            plot_item.legend.clear()

        if len(elapsed_seconds) == 1:
            threshold_x = [elapsed_seconds[0], elapsed_seconds[0] + 1.0]
        else:
            threshold_x = [min(elapsed_seconds), max(elapsed_seconds)]

        self.current_curve = plot_item.plot(
            elapsed_seconds,
            current_values,
            pen=pg.mkPen("#3b82f6", width=2),
            name="Current",
        )
        self.current_curve.setClipToView(True)
        self.current_curve.setDownsampling(auto=True, method="peak")

        sleep_limit_ma = self.current_limit_edit.value()
        wake_limit_ma = self.wake_limit_edit.value()
        self.sleep_threshold_curve = plot_item.plot(
            threshold_x,
            [sleep_limit_ma, sleep_limit_ma],
            pen=pg.mkPen("#22c55e", width=1.5, style=Qt.DashLine),
            name="Sleep threshold",
        )
        self.wake_threshold_curve = plot_item.plot(
            threshold_x,
            [wake_limit_ma, wake_limit_ma],
            pen=pg.mkPen("#f97316", width=1.5, style=Qt.DashLine),
            name="Wake-up threshold",
        )
        plot_item.enableAutoRange()
        self.chart_placeholder.hide()
        self.current_plot.show()

    def _clear_current_chart(self):
        if not hasattr(self, "current_plot"):
            return
        plot_item = self.current_plot.getPlotItem()
        plot_item.clear()
        if plot_item.legend is not None:
            plot_item.legend.clear()
        self.current_curve = None
        self.sleep_threshold_curve = None
        self.wake_threshold_curve = None
        self.current_plot.hide()
        self.chart_placeholder.show()

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
        QApplication.clipboard().setText(self._summary_to_text())

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
        rows = []
        for key, label in self.summary_labels.items():
            rows.append(
                f"{label.text()}\t{self.summary_values[key].text()}"
            )
        return "\n".join(rows)

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
            self.btn_run,
            self.btn_export,
            self.btn_copy_chart,
            self.btn_copy_data_review,
            self.btn_copy_summary,
            self.btn_clear,
        ):
            widget.fn_refresh_theme()

        spinbox_style = fn_spinbox_style()
        for spinbox in (
            self.current_limit_edit,
            self.sleep_duration_edit,
            self.wake_limit_edit,
            self.wake_duration_edit,
        ):
            spinbox.setStyleSheet(spinbox_style)

        for label in self.findChildren(PrimaryLabel):
            label.fn_refresh_theme()

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
