from __future__ import annotations

import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QGroupBox

from core.q_current_analysis import QCurrentAnalysisResult, parse_q_current_timestamp
from gui.themes.theme_manager import ThemeManager
from gui.widgets.controls.primary_label import PrimaryLabel


PLACEHOLDER_VALUE = "\u2014"
NOT_AVAILABLE_VALUE = "N/A"


class QCurrentSummaryWidget(QGroupBox):

    def __init__(self, parent=None):
        super().__init__("Summary", parent)
        self.summary_labels = {}
        self.summary_values = {}
        self._rows = (
            ("result_status", "Result"),
            ("average_sleep_current_ma", "Average Sleep Current"),
            ("minimum_sleep_current_ma", "Min Sleep Current"),
            ("maximum_sleep_current_ma", "Max Sleep Current"),
            ("wake_up_event_count", "Wake-up Events"),
            ("total_wake_up_duration_s", "Total Wake-up Duration"),
            ("average_wake_up_duration_s", "Average Wake-up Duration"),
            ("maximum_wake_up_duration_s", "Max Wake-up Duration"),
            ("average_wake_up_interval_s", "Average Wake-up Interval"),
            ("minimum_wake_up_interval_s", "Min Wake-up Interval"),
            ("maximum_wake_up_interval_s", "Max Wake-up Interval"),
            ("longest_continuous_sleep_s", "Longest Continuous Sleep"),
            ("source_start_time", "Start Time"),
            ("source_end_time", "End Time"),
            ("duration_s", "Duration"),
            ("total_samples", "Total Samples"),
            ("sample_interval_s", "Sample Interval"),
        )
        self._setup_ui()
        self.clear_result()
        self.fn_refresh_theme()

    def _setup_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(6)

        for row, (key, label_text) in enumerate(self._rows):
            label = PrimaryLabel(label_text)
            value = PrimaryLabel(PLACEHOLDER_VALUE)

            label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )

            value.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )

            value.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            value.setWordWrap(True)

            self.summary_labels[key] = label
            self.summary_values[key] = value

            layout.addWidget(label, row, 0)
            layout.addWidget(value, row, 1)

        
        
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(len(self._rows), 1)

    def set_result(self, result: QCurrentAnalysisResult):
        self.summary_values["result_status"].setText(result.result_status)
        self.summary_values["average_sleep_current_ma"].setText(
            self._format_current(result.average_sleep_current_ma)
        )
        self.summary_values["minimum_sleep_current_ma"].setText(
            self._format_current(result.minimum_sleep_current_ma)
        )
        self.summary_values["maximum_sleep_current_ma"].setText(
            self._format_current(result.maximum_sleep_current_ma)
        )
        self.summary_values["wake_up_event_count"].setText(
            str(result.wake_up_event_count)
        )
        self.summary_values["total_wake_up_duration_s"].setText(
            self._format_duration(result.total_wake_up_duration_s)
        )
        self.summary_values["average_wake_up_duration_s"].setText(
            self._format_duration(result.average_wake_up_duration_s)
        )
        self.summary_values["maximum_wake_up_duration_s"].setText(
            self._format_duration(result.maximum_wake_up_duration_s)
        )
        self.summary_values["average_wake_up_interval_s"].setText(
            self._format_duration(result.average_wake_up_interval_s)
        )
        self.summary_values["minimum_wake_up_interval_s"].setText(
            self._format_duration(result.minimum_wake_up_interval_s)
        )
        self.summary_values["maximum_wake_up_interval_s"].setText(
            self._format_duration(result.maximum_wake_up_interval_s)
        )
        self.summary_values["longest_continuous_sleep_s"].setText(
            self._format_duration(result.longest_continuous_sleep_s)
        )
        self.summary_values["source_start_time"].setText(
            self._format_source_time(result.source_start_time)
        )
        self.summary_values["source_end_time"].setText(
            self._format_source_time(result.source_end_time)
        )
        self.summary_values["duration_s"].setText(
            self._format_duration(result.duration_s)
        )
        self.summary_values["total_samples"].setText(str(result.total_samples))
        self.summary_values["sample_interval_s"].setText(
            self._format_duration(result.sample_interval_s)
        )
        self.fn_refresh_theme()

    def clear_result(self):
        for value in self.summary_values.values():
            value.setText(PLACEHOLDER_VALUE)
        self.fn_refresh_theme()

    def to_text(self) -> str:
        value = self._display_value
        return "\n".join([
            "SUMMARY",
            "",
            f"RESULT: {value('result_status')}",
            "",
            "CURRENT STATISTICS",
            f"Average Sleep Current: {value('average_sleep_current_ma')}",
            f"Minimum Sleep Current: {value('minimum_sleep_current_ma')}",
            f"Maximum Sleep Current: {value('maximum_sleep_current_ma')}",
            "",
            "WAKE-UP STATISTICS",
            f"Wake-up Events: {value('wake_up_event_count')}",
            f"Total Wake-up Duration: {value('total_wake_up_duration_s')}",
            f"Average Wake-up Duration: {value('average_wake_up_duration_s')}",
            f"Maximum Wake-up Duration: {value('maximum_wake_up_duration_s')}",
            f"Average Wake-up Interval: {value('average_wake_up_interval_s')}",
            f"Minimum Wake-up Interval: {value('minimum_wake_up_interval_s')}",
            f"Maximum Wake-up Interval: {value('maximum_wake_up_interval_s')}",
            f"Longest Continuous Sleep: {value('longest_continuous_sleep_s')}",
            "",
            "TEST INFORMATION",
            f"Start Time: {value('source_start_time')}",
            f"End Time: {value('source_end_time')}",
            f"Duration: {value('duration_s')}",
            f"Total Samples: {value('total_samples')}",
            f"Sample Interval: {value('sample_interval_s')}",
        ])

    def _display_value(self, key: str) -> str:
        value = self.summary_values[key].text()
        if value == PLACEHOLDER_VALUE:
            return NOT_AVAILABLE_VALUE
        return value

    def fn_refresh_theme(self):
        colors = ThemeManager.fn_colors()
        default_style = f"""
            QLabel {{
                color: {colors.TEXT};
                background: transparent;
                font-size: 10pt;
            }}
        """
        for label in self.summary_labels.values():
            label.fn_refresh_theme()
        for key, value in self.summary_values.items():
            value.fn_refresh_theme()
            if key != "result_status":
                value.setStyleSheet(default_style)

        status_label = self.summary_values.get("result_status")
        if status_label is None:
            return
        status = status_label.text()
        if status == "PASSED":
            status_color = colors.SUCCESS
        elif status == "FAILED":
            status_color = colors.DANGER
        else:
            status_color = colors.TEXT
        status_label.setStyleSheet(
            f"""
            QLabel {{
                color: {status_color};
                background: transparent;
                font-size: 10pt;
                font-weight: 700;
            }}
            """
        )

    @staticmethod
    def _format_current(value: float | None) -> str:
        if value is None:
            return NOT_AVAILABLE_VALUE
        return f"{value:.2f} mA"

    @staticmethod
    def _format_source_time(value: str | None) -> str:
        if value is None:
            return NOT_AVAILABLE_VALUE
        text = str(value).strip()
        if not text:
            return NOT_AVAILABLE_VALUE
        try:
            parsed = parse_q_current_timestamp(text)
        except ValueError:
            parsed = None
        if hasattr(parsed, "strftime"):
            return parsed.strftime("%H:%M:%S")

        match = re.search(r"\b(\d{1,2}:\d{2}:\d{2})(?:\.\d+)?\b", text)
        if match:
            return match.group(1)
        return text

    @staticmethod
    def _format_time(value: float | None) -> str:
        if value is None:
            return NOT_AVAILABLE_VALUE
        return f"{value:.1f} (s)"

    @staticmethod
    def _format_duration(value: float | None) -> str:
        if value is None:
            return NOT_AVAILABLE_VALUE
        if value < 60.0:
            return f"{value:.1f} (s)"
        minutes, seconds = divmod(value, 60.0)
        if minutes < 60.0:
            return f"{int(minutes)} min {seconds:.1f} (s)"
        hours, minutes = divmod(minutes, 60.0)
        return f"{int(hours)} h {int(minutes)} min {seconds:.1f} (s)"
