from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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
)

from core.sleep_current_database import (
    default_dataset_name,
    get_dataset_by_name,
    get_samples,
    import_dataset,
    initialize_database,
    list_datasets,
    normalize_current_data,
    replace_dataset,
    resolve_database_path,
)
from gui.themes.styles.containers.groupbox_style import fn_groupbox_style
from gui.themes.styles.controls.spinbox_style import fn_spinbox_style
from gui.themes.theme_manager import ThemeManager
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_combobox import PrimaryComboBox
from gui.widgets.controls.primary_label import PrimaryLabel
from gui.widgets.controls.primary_lineedit import PrimaryLineEdit


PLACEHOLDER_VALUE = "\u2014"
SOURCE_FILE_PLACEHOLDER = "Select current data file (*.csv, *.xlsx)"
SUPPORTED_SOURCE_EXTENSIONS = {".csv", ".xlsx"}
SOURCE_FILE_FILTER = (
    "Supported Files (*.csv *.xlsx);;"
    "CSV Files (*.csv);;"
    "Excel Files (*.xlsx)"
)


class QCurrentTab(QWidget):

    def __init__(self, database_file: str | Path | None = None):
        super().__init__()

        self._theme_widgets = []
        self._database_file = database_file
        self.current_import = None
        self.current_samples = []
        self.current_database_path = None
        self._setup_ui()
        self._initialize_database()
        self._refresh_dataset_combo()
        self._connect_signals()
        self.fn_refresh_theme()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        self.settings_group = self._create_settings_group()
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)

        self.information_group = self._create_information_group()
        self.center_splitter = self._create_center_splitter()
        self.right_panel = self._create_right_panel()

        self.main_splitter.addWidget(self.information_group)
        self.main_splitter.addWidget(self.center_splitter)
        self.main_splitter.addWidget(self.right_panel)
        self.main_splitter.setSizes([260, 620, 220])

        main_layout.addWidget(self.settings_group)
        main_layout.addWidget(self.main_splitter, 1)

    def _initialize_database(self):
        self.current_database_path = initialize_database(self._database_file)

    def _connect_signals(self):
        self.browse_button.clicked.connect(self.browse_current_file)
        self.import_button.clicked.connect(self.import_current_file)

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

        self.dataset_combo = PrimaryComboBox()
        self.dataset_combo.setObjectName("dataset_combo")
        self.dataset_combo.setMinimumWidth(220)
        self.dataset_combo.setFixedHeight(36)

        self.import_button = PrimaryButton(
            "Import",
            width=90,
            height=36,
        )
        self.import_button.setObjectName("import_button")
        self.import_button.setEnabled(False)

        self.current_limit_label = PrimaryLabel(
            "Standard current (mA)"
        )

        self.current_limit_edit = QDoubleSpinBox()
        self.current_limit_edit.setObjectName("current_limit_edit")
        self.current_limit_edit.setDecimals(2)
        self.current_limit_edit.setMinimum(0.0)
        self.current_limit_edit.setMaximum(1000000.0)
        self.current_limit_edit.setSingleStep(0.10)
        self.current_limit_edit.setValue(30.00)
        self.current_limit_edit.setFixedWidth(110)
        self.current_limit_edit.setMinimumHeight(36)
        self.current_limit_edit.lineEdit().setAlignment(Qt.AlignCenter)

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
        result_layout.addWidget(self.analysis_result_label)
        result_layout.addWidget(self.analysis_result_edit)
        result_layout.addStretch(1)

        self.settings_layout.addLayout(result_layout, 1, 0, 1, 4)

        return group

    def _create_information_group(self):
        group = QGroupBox("Analysis Information")
        layout = QGridLayout(group)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(8)

        self.info_values = {}
        rows = (
            ("sample_count", "Samples"),
            ("duration", "Duration"),
            ("min_current", "Min Current"),
            ("max_current", "Max Current"),
            ("avg_current", "Average Current"),
            ("status", "Status"),
        )
        for row, (key, label_text) in enumerate(rows):
            layout.addWidget(PrimaryLabel(label_text), row, 0)
            value_label = self._create_value_label()
            self.info_values[key] = value_label
            layout.addWidget(value_label, row, 1)

        layout.setColumnStretch(1, 1)
        layout.setRowStretch(len(rows), 1)
        return group

    def _create_center_splitter(self):
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)

        self.chart_group = QGroupBox("Current Chart")
        chart_layout = QVBoxLayout(self.chart_group)
        chart_layout.setContentsMargins(12, 16, 12, 12)
        self.chart_placeholder = self._create_placeholder_panel()
        chart_layout.addWidget(self.chart_placeholder, 1)

        self.review_group = QGroupBox("Data Review")
        review_layout = QVBoxLayout(self.review_group)
        review_layout.setContentsMargins(12, 16, 12, 12)
        self.review_placeholder = self._create_placeholder_panel()
        review_layout.addWidget(self.review_placeholder, 1)

        splitter.addWidget(self.chart_group)
        splitter.addWidget(self.review_group)
        splitter.setSizes([420, 240])
        return splitter

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
        self.btn_clear = PrimaryButton("CLEAR")

        for button in (
            self.btn_run,
            self.btn_export,
            self.btn_copy_chart,
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

        self.summary_values = {}
        rows = (
            ("peak", "Peak"),
            ("rms", "RMS"),
            ("energy", "Energy"),
            ("window", "Window"),
        )
        for row, (key, label_text) in enumerate(rows):
            layout.addWidget(PrimaryLabel(label_text), row, 0)
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
        self.import_button.setEnabled(self._is_valid_source_file(path))

    def import_current_file(self):
        source_path = Path(self.source_file_edit.text()).expanduser()
        try:
            source_path = source_path.resolve()
            normalized = normalize_current_data(source_path)
            dataset_name = default_dataset_name(source_path)
            existing_dataset = get_dataset_by_name(
                dataset_name,
                self._database_file,
            )
        except Exception as error:
            self.analysis_result_edit.setText("IMPORT FAILED")
            QMessageBox.warning(self, "Q current Import", str(error))
            return

        try:
            if existing_dataset is not None:
                response = QMessageBox.question(
                    self,
                    "Replace Dataset",
                    (
                        f"Dataset '{dataset_name}' already exists.\n"
                        "Replace it with the selected file?"
                    ),
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                    QMessageBox.No,
                )
                if response != QMessageBox.Yes:
                    return

                result = replace_dataset(
                    existing_dataset.id,
                    dataset_name,
                    source_path,
                    normalized.rows,
                    self._database_file,
                    detected_channel=normalized.detected_channel,
                )
            else:
                result = import_dataset(
                    dataset_name,
                    source_path,
                    normalized.rows,
                    self._database_file,
                    detected_channel=normalized.detected_channel,
                )
        except Exception as error:
            self.analysis_result_edit.setText("IMPORT FAILED")
            QMessageBox.warning(self, "Q current Import", str(error))
            return

        self.current_import = result
        self.current_samples = get_samples(result.dataset.id, self._database_file)
        self.current_database_path = resolve_database_path(self._database_file)
        self._refresh_dataset_combo(result.dataset.id)
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

    def _refresh_dataset_combo(self, desired_dataset_id: int | None = None):
        selected_id = desired_dataset_id
        if selected_id is None:
            selected_id = self.dataset_combo.currentData()

        self.dataset_combo.clear()
        for dataset in list_datasets(self._database_file):
            self.dataset_combo.addItem(dataset.name, dataset.id)

        if selected_id is not None:
            index = self.dataset_combo.findData(selected_id)
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
            self.information_group,
            self.chart_group,
            self.review_group,
            self.summary_group,
        ):
            group.setStyleSheet(group_style)

        for widget in (
            self.source_file_edit,
            self.analysis_result_edit,
            self.dataset_combo,
            self.browse_button,
            self.import_button,
            self.btn_run,
            self.btn_export,
            self.btn_copy_chart,
            self.btn_clear,
        ):
            widget.fn_refresh_theme()

        self.current_limit_edit.setStyleSheet(
            fn_spinbox_style()
        )

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
            if label in (self.chart_placeholder, self.review_placeholder):
                label.setStyleSheet(placeholder_style)
            else:
                label.setStyleSheet(value_style)
