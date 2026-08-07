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


class ExportVehicleDialog(QDialog):

    def __init__(
        self,
        vehicle_name: str,
        ecu_text: str,
        parent=None,
    ):

        super().__init__(parent)

        self.setWindowTitle("Export Vehicle")

        self.resize(520, 420)

        self._vehicle_name = vehicle_name

        self._ecu_text = ecu_text

        self._setup_ui()

        self._connect_signals()

        self.fn_refresh_theme()

    def _setup_ui(self):

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(16, 16, 16, 16)

        main_layout.setSpacing(12)

        main_layout.addWidget(
            PrimaryLabel("Format")
        )

        main_layout.addWidget(
            PrimaryLabel("ECU|Request|Response")
        )

        main_layout.addSpacing(8)

        main_layout.addWidget(
            PrimaryLabel(self._vehicle_name)
        )

        self.txt_ecus = QPlainTextEdit()

        self.txt_ecus.setPlainText(
            self._ecu_text
        )

        self.txt_ecus.setReadOnly(True)

        main_layout.addWidget(
            self.txt_ecus,
            1,
        )

        button_layout = QHBoxLayout()

        button_layout.addStretch()

        self.btn_close = CancelButton(
            "Close",
            width=100,
        )

        self.btn_copy = PrimaryButton(
            "Copy",
            width=100,
        )

        button_layout.addWidget(
            self.btn_close
        )

        button_layout.addWidget(
            self.btn_copy
        )

        main_layout.addLayout(
            button_layout
        )

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

        return self.txt_ecus.toPlainText()

    def fn_refresh_theme(self):

        colors = ThemeManager.fn_colors()

        self.txt_ecus.setStyleSheet(
            f"""
            QPlainTextEdit {{
                background: {colors.WINDOW};
                color: {colors.TEXT};
                border: 1px solid {colors.BORDER};
                border-radius: 6px;
                padding: 8px;
                font-family: "Consolas";
                font-size: 10pt;
            }}
            """
        )

        self.btn_close.fn_refresh_theme()

        self.btn_copy.fn_refresh_theme()
