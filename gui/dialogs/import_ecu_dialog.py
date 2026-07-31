from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
)

from gui.themes.theme_manager import ThemeManager
from gui.widgets.controls.cancel_button import CancelButton
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_label import PrimaryLabel
from models.ecu import ECU


class ImportECUDialog(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle("Import ECU List")

        self.resize(520, 420)

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
            PrimaryLabel("Example")
        )

        main_layout.addWidget(
            PrimaryLabel(
                "BCM|681|601\n"
                "ACM|688|608\n"
                "MHU|684|604"
            )
        )

        main_layout.addSpacing(8)

        main_layout.addWidget(
            PrimaryLabel("Paste here")
        )

        self.txt_ecus = QPlainTextEdit()

        self.txt_ecus.setPlaceholderText(
            "BCM|681|601\nACM|688|608"
        )

        main_layout.addWidget(
            self.txt_ecus,
            1,
        )

        button_layout = QHBoxLayout()

        button_layout.addStretch()

        self.btn_cancel = CancelButton(
            "Cancel",
            width=100,
        )

        self.btn_import = PrimaryButton(
            "Import",
            width=100,
        )

        button_layout.addWidget(
            self.btn_cancel
        )

        button_layout.addWidget(
            self.btn_import
        )

        main_layout.addLayout(
            button_layout
        )

    def _connect_signals(self):

        self.btn_cancel.clicked.connect(
            self.reject
        )

        self.btn_import.clicked.connect(
            self._on_import_clicked
        )

    def _on_import_clicked(self):

        try:

            self.fn_ecus()

        except ValueError as error:

            QMessageBox.warning(
                self,
                "Import ECU List",
                str(error),
            )

            return

        self.accept()

    def fn_ecus(self) -> list[ECU]:

        lines = [
            line.strip()
            for line in self.txt_ecus.toPlainText().splitlines()
            if line.strip()
        ]

        if not lines:

            raise ValueError(
                "Please paste at least one ECU."
            )

        ecus = []
        seen_names = set()

        for index, line in enumerate(lines, start=1):

            parts = [
                item.strip()
                for item in line.split("|")
            ]

            if len(parts) != 3:

                raise ValueError(
                    f"Line {index} must use format ECU|Request|Response."
                )

            ecu_name, request_id, response_id = parts

            if not ecu_name:

                raise ValueError(
                    f"Line {index} has an empty ECU name."
                )

            if ecu_name.lower() in seen_names:

                raise ValueError(
                    f"Duplicate ECU in pasted list: {ecu_name}."
                )

            seen_names.add(
                ecu_name.lower()
            )

            ecus.append(
                ECU(
                    name=ecu_name,
                    request_id=request_id,
                    response_id=response_id,
                )
            )

        return ecus

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

        self.btn_cancel.fn_refresh_theme()

        self.btn_import.fn_refresh_theme()
