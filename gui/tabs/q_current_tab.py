from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QLabel,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from gui.themes.styles.containers.groupbox_style import fn_groupbox_style
from gui.themes.theme_manager import ThemeManager
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_combobox import PrimaryComboBox
from gui.widgets.controls.primary_label import PrimaryLabel


PLACEHOLDER_VALUE = "â€”"


class QCurrentTab(QWidget):

    def __init__(self):
        super().__init__()

        self._theme_widgets = []
        self._setup_ui()
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

    def _create_settings_group(self):
        group = QGroupBox("Analysis Settings")
        layout = QGridLayout(group)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)

        self.vehicle_selector = PrimaryComboBox()
        self.vehicle_selector.addItem(PLACEHOLDER_VALUE)
        self.ecu_selector = PrimaryComboBox()
        self.ecu_selector.addItem(PLACEHOLDER_VALUE)
        self.channel_selector = PrimaryComboBox()
        self.channel_selector.addItem(PLACEHOLDER_VALUE)
        self.file_value = self._create_value_label()

        layout.addWidget(PrimaryLabel("Vehicle"), 0, 0)
        layout.addWidget(self.vehicle_selector, 0, 1)
        layout.addWidget(PrimaryLabel("ECU"), 0, 2)
        layout.addWidget(self.ecu_selector, 0, 3)
        layout.addWidget(PrimaryLabel("Channel"), 0, 4)
        layout.addWidget(self.channel_selector, 0, 5)
        layout.addWidget(PrimaryLabel("Source"), 1, 0)
        layout.addWidget(self.file_value, 1, 1, 1, 5)

        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)
        layout.setColumnStretch(5, 1)
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
            self.vehicle_selector,
            self.ecu_selector,
            self.channel_selector,
            self.btn_run,
            self.btn_export,
            self.btn_copy_chart,
            self.btn_clear,
        ):
            widget.fn_refresh_theme()

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