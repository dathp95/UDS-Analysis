from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QGroupBox

from core.q_current_analysis import QCurrentAnalysisResult
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
            ("start_time_s", "Start Time"),
            ("end_time_s", "End Time"),
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
        self.summary_values["start_time_s"].setText(
            self._format_time(result.start_time_s)
        )
        self.summary_values["end_time_s"].setText(
            self._format_time(result.end_time_s)
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
        rows = []
        for key, label in self.summary_labels.items():
            rows.append(f"{label.text()}\t{self.summary_values[key].text()}")
        return "\n".join(rows)

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
    def _format_time(value: float | None) -> str:
        if value is None:
            return NOT_AVAILABLE_VALUE
        return f"{value:.3f} s"

    @staticmethod
    def _format_duration(value: float | None) -> str:
        if value is None:
            return NOT_AVAILABLE_VALUE
        if value < 60.0:
            return f"{value:.3f} s"
        minutes, seconds = divmod(value, 60.0)
        if minutes < 60.0:
            return f"{int(minutes)} min {seconds:.3f} s"
        hours, minutes = divmod(minutes, 60.0)
        return f"{int(hours)} h {int(minutes)} min {seconds:.3f} s"
