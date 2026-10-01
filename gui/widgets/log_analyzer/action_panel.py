from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPlainTextEdit,
    QGroupBox,
    QProgressBar,
)

from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_label import PrimaryLabel
from gui.themes.theme_manager import ThemeManager
from gui.themes.styles.controls.scrollbar_style import fn_apply_scrollbar_style


class ActionPanel(QWidget):
    analyze_clicked = Signal()
    export_clicked = Signal()
    copy_clicked = Signal()
    clear_clicked = Signal()

    QUICK_FILTER_PLACEHOLDER = {
        "Name": "-",
        "ECU": "-",
        "Request": "-",
        "Response": "-",
    }
    TRANSACTION_PLACEHOLDER = {
        "ECU": "-",
        "Time": "-",
        "Activity": "-",
        "Request": "-",
        "Response": "-",
        "RT (ms)": "-",
        "Status": "-",
    }

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._connect_signals()
        self.fn_clear_detail_panels()
        self.fn_set_analysis_ready()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.grp_analysis_progress = self._fn_create_detail_group(
            "Analysis Progress"
        )
        self.lbl_analysis_status = PrimaryLabel("Ready")
        self.progress_analysis = QProgressBar()
        self.progress_analysis.setRange(0, 100)
        self.progress_analysis.setValue(0)
        self.progress_analysis.setTextVisible(False)
        self.progress_analysis.setMaximumHeight(12)
        self.grp_analysis_progress.layout().addWidget(
            self.lbl_analysis_status
        )
        self.grp_analysis_progress.layout().addWidget(
            self.progress_analysis
        )

        self.btn_run = PrimaryButton(
            "Analyze",
            width=160,
            height=40,
        )

        self.btn_export = PrimaryButton(
            "EXPORT",
            width=160,
            height=40,
        )

        self.btn_copy = PrimaryButton(
            "COPY ASC DATA",
            width=160,
            height=40,
        )

        self.btn_clear = PrimaryButton(
            "CLEAR TABLE",
            width=160,
            height=40,
        )

        self.grp_quick_filter_info = self._fn_create_detail_group(
            "Quick Filter"
        )
        self.txt_quick_filter_info = QPlainTextEdit()
        self._fn_setup_detail_text(self.txt_quick_filter_info)
        self.grp_quick_filter_info.layout().addWidget(
            self.txt_quick_filter_info
        )

        self.grp_transaction_info = self._fn_create_detail_group(
            "Transaction"
        )
        self.txt_transaction_info = QPlainTextEdit()
        self._fn_setup_detail_text(self.txt_transaction_info)
        self.grp_transaction_info.layout().addWidget(
            self.txt_transaction_info
        )

        layout.addWidget(self.grp_analysis_progress)
        layout.addWidget(self.btn_run)
        layout.addWidget(self.btn_export)
        layout.addWidget(self.btn_copy)
        layout.addWidget(self.btn_clear)

        layout.addWidget(
            self.grp_quick_filter_info,
            2,
        )
        layout.addWidget(
            self.grp_transaction_info,
            3,
        )

    def _fn_create_detail_group(
            self,
            title: str,
        ) -> QGroupBox:
        group = QGroupBox(title)
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(8, 8, 8, 8)
        group_layout.setSpacing(6)
        return group

    @staticmethod
    def _fn_setup_detail_text(
            text_edit: QPlainTextEdit,
        ) -> None:
        text_edit.setReadOnly(True)
        text_edit.setLineWrapMode(
            QPlainTextEdit.WidgetWidth
        )
        text_edit.setMinimumHeight(80)

    def _connect_signals(self):
        self.btn_run.clicked.connect(
            self.analyze_clicked.emit
        )
        self.btn_export.clicked.connect(
            self.export_clicked.emit
        )
        self.btn_copy.clicked.connect(
            self.copy_clicked.emit
        )
        self.btn_clear.clicked.connect(
            self.clear_clicked.emit
        )

    def _fn_enable_buttons(
            self,
            run: bool,
            export: bool,
            copy: bool,
            clear: bool,
        ):
        self.btn_run.setEnabled(run)
        self.btn_export.setEnabled(export)
        self.btn_copy.setEnabled(copy)
        self.btn_clear.setEnabled(clear)

    def fn_set_startup_state(self):
        self.btn_run.setText("Analyze")
        self._fn_enable_buttons(
            run=False,
            export=False,
            copy=False,
            clear=False,
        )

    def fn_set_file_loaded_state(self) -> None:
        """Update action buttons after the user selects a log file."""

        self.btn_run.setText("Analyze")
        self._fn_enable_buttons(
            run=True,
            export=False,
            copy=False,
            clear=False,
        )

    def fn_set_analyzed_state(self) -> None:
        """Update action buttons after analysis is complete."""

        self.btn_run.setText("Analyze")
        self._fn_enable_buttons(
            run=True,
            export=True,
            copy=True,
            clear=True,
        )

    def fn_set_analysis_ready(self) -> None:
        self.lbl_analysis_status.setText("Ready")
        self.progress_analysis.setRange(0, 100)
        self.progress_analysis.setValue(0)
        self.btn_run.setText("Analyze")

    def fn_set_analysis_started(self) -> None:
        self.lbl_analysis_status.setText("Starting analysis...")
        self.progress_analysis.setRange(0, 0)
        self.btn_run.setText("ANALYZING...")
        self._fn_enable_buttons(
            run=False,
            export=False,
            copy=False,
            clear=False,
        )

    def fn_set_analysis_status(
            self,
            text: str,
        ) -> None:
        if text:
            self.lbl_analysis_status.setText(text)

    def fn_set_analysis_completed(self) -> None:
        self.lbl_analysis_status.setText("Completed")
        self.progress_analysis.setRange(0, 100)
        self.progress_analysis.setValue(100)
        self.btn_run.setText("Analyze")

    def fn_set_analysis_failed(
            self,
            message: str | None = None,
        ) -> None:
        self.lbl_analysis_status.setText("Failed")
        self.progress_analysis.setRange(0, 100)
        self.progress_analysis.setValue(0)
        self.btn_run.setText("Analyze")

    def fn_set_quick_filter_info(
            self,
            filter_data: dict,
        ) -> None:
        """Show selected quick filter details."""

        if not isinstance(filter_data, dict):
            self.fn_clear_quick_filter_info()
            return

        filters = filter_data.get("filters", {})

        if not isinstance(filters, dict):
            filters = {}

        self.txt_quick_filter_info.setPlainText(
            self._fn_format_details(
                {
                    "Name": self._fn_text_value(filter_data, "name"),
                    "ECU": self._fn_text_value(filters, "ecu"),
                    "Request": self._fn_text_value(filters, "request"),
                    "Response": self._fn_text_value(filters, "response"),
                }
            )
        )

    def fn_set_quick_filter_log(
            self,
            filter_data: dict,
        ) -> None:
        """Backward-compatible wrapper for quick filter info."""

        self.fn_set_quick_filter_info(filter_data)

    def fn_set_transaction_info(
            self,
            row_data: dict,
        ) -> None:
        """Show selected result table row details."""

        if not isinstance(row_data, dict) or not row_data:
            self.fn_clear_transaction_info()
            return

        self.txt_transaction_info.setPlainText(
            self._fn_format_details(
                {
                    "ECU": self._fn_text_value(row_data, "ECU"),
                    "Time": self._fn_text_value(row_data, "Time"),
                    "Activity": self._fn_text_value(row_data, "Activity"),
                    "Request": self._fn_text_value(row_data, "Request"),
                    "Response": self._fn_text_value(row_data, "Response"),
                    "RT (ms)": self._fn_text_value(row_data, "RT (ms)"),
                    "Status": self._fn_text_value(row_data, "Status"),
                }
            )
        )

    def fn_clear_quick_filter_info(self) -> None:
        self.txt_quick_filter_info.setPlainText(
            self._fn_format_details(self.QUICK_FILTER_PLACEHOLDER)
        )

    def fn_clear_transaction_info(self) -> None:
        self.txt_transaction_info.setPlainText(
            self._fn_format_details(self.TRANSACTION_PLACEHOLDER)
        )

    def fn_clear_detail_panels(self) -> None:
        self.fn_clear_quick_filter_info()
        self.fn_clear_transaction_info()

    def fn_clear_working_log(self) -> None:
        """Backward-compatible wrapper for detail reset."""

        self.fn_clear_detail_panels()

    @staticmethod
    def _fn_format_details(
            details: dict,
        ) -> str:
        return "\n\n".join(
            f"{key}: {value}"
            for key, value in details.items()
        )

    @staticmethod
    def _fn_text_value(
            data: dict,
            key: str,
        ) -> str:
        value = data.get(key, "")

        if value is None or value == "":
            return "-"

        return str(value)

    def fn_refresh_theme(self):
        self.btn_run.fn_refresh_theme()
        self.btn_export.fn_refresh_theme()
        self.btn_copy.fn_refresh_theme()
        self.btn_clear.fn_refresh_theme()
        self.lbl_analysis_status.fn_refresh_theme()

        colors = ThemeManager.fn_colors()

        group_style = (
            f"""
            QGroupBox {{
                color: {colors.TEXT};
                border: 1px solid {colors.BORDER};
                border-radius: 6px;
                margin-top: 8px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
                background: {colors.WINDOW};
            }}
            """
        )

        text_style = (
            f"""
            QPlainTextEdit {{
                background: {colors.WINDOW};
                color: {colors.TEXT};
                border: 1px solid {colors.BORDER};
                border-radius: 6px;
                padding: 8px;
                font-family: Consolas;
                font-size: 10pt;
            }}
            """
        )

        progress_style = (
            f"""
            QProgressBar {{
                background: {colors.WINDOW};
                border: 1px solid {colors.BORDER};
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: {colors.SUCCESS};
                border-radius: 3px;
            }}
            """
        )

        self.grp_analysis_progress.setStyleSheet(group_style)
        self.grp_quick_filter_info.setStyleSheet(group_style)
        self.grp_transaction_info.setStyleSheet(group_style)
        self.txt_quick_filter_info.setStyleSheet(text_style)
        self.txt_transaction_info.setStyleSheet(text_style)
        self.progress_analysis.setStyleSheet(progress_style)

        fn_apply_scrollbar_style(self.txt_quick_filter_info)
        fn_apply_scrollbar_style(self.txt_transaction_info)
