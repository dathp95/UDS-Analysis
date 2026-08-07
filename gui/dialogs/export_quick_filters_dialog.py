from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QPlainTextEdit,
    QVBoxLayout,
)

from gui.themes.theme_manager import ThemeManager
from gui.widgets.controls.cancel_button import CancelButton
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_label import PrimaryLabel


class ExportQuickFiltersDialog(QDialog):

    def __init__(
        self,
        filters_text: str,
        parent=None,
    ):

        super().__init__(parent)

        self.setWindowTitle("Export Quick Access Filters")

        self.resize(620, 440)

        self._filters_text = filters_text

        self._setup_ui()

        self._connect_signals()

        self.fn_refresh_theme()

    def _setup_ui(self):

        layout = QVBoxLayout(self)

        layout.addWidget(
            PrimaryLabel("Format: Name|ECU|Request|Response")
        )

        self.txt_filters = QPlainTextEdit()

        self.txt_filters.setPlainText(
            self._filters_text
        )

        self.txt_filters.setReadOnly(True)

        layout.addWidget(
            self.txt_filters,
            1,
        )

        buttons = QHBoxLayout()

        buttons.addStretch()

        self.btn_close = CancelButton(
            "Close",
            width=100,
        )

        self.btn_copy = PrimaryButton(
            "Copy",
            width=100,
        )

        buttons.addWidget(
            self.btn_close
        )

        buttons.addWidget(
            self.btn_copy
        )

        layout.addLayout(buttons)

    def _connect_signals(self):

        self.btn_close.clicked.connect(
            self.reject
        )

        self.btn_copy.clicked.connect(
            self._on_copy_clicked
        )

    def _on_copy_clicked(self):

        QApplication.clipboard().setText(
            self.fn_export_text()
        )

    def fn_export_text(self) -> str:

        return self.txt_filters.toPlainText()

    def fn_refresh_theme(self):

        colors = ThemeManager.fn_colors()

        self.txt_filters.setStyleSheet(
            f"QPlainTextEdit {{ background: {colors.WINDOW}; color: {colors.TEXT}; }}"
        )

        self.btn_close.fn_refresh_theme()

        self.btn_copy.fn_refresh_theme()
