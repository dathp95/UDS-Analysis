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


class ImportDisplayNamesDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Import Display Name")
        self.resize(620, 460)

        self._setup_ui()
        self._connect_signals()
        self.fn_refresh_theme()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        main_layout.addWidget(PrimaryLabel("Format"))
        main_layout.addWidget(PrimaryLabel("Payload | Display Name"))
        main_layout.addSpacing(8)
        main_layout.addWidget(PrimaryLabel("Example"))
        main_layout.addWidget(
            PrimaryLabel(
                "22 F1 20| Global Time\n"
                "22 F1 22 | Vehicle supply Voltage\n"
                "22 D1 00   | Key Sw Number"
            )
        )
        main_layout.addSpacing(8)
        main_layout.addWidget(PrimaryLabel("Paste rules here"))

        self.txt_rules = QPlainTextEdit()
        self.txt_rules.setPlaceholderText(
            "22 F1 20| Global Time\n22 F1 22| Vehicle supply Voltage"
        )
        main_layout.addWidget(self.txt_rules, 1)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.btn_cancel = CancelButton("Cancel", width=100)
        self.btn_import = PrimaryButton("Import", width=100)

        button_layout.addWidget(self.btn_cancel)
        button_layout.addWidget(self.btn_import)
        main_layout.addLayout(button_layout)

    def _connect_signals(self):
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_import.clicked.connect(self._on_import_clicked)

    def _on_import_clicked(self):
        try:
            self.fn_rules()
        except ValueError as error:
            QMessageBox.warning(self, "Import Display Name", str(error))
            return

        self.accept()

    def fn_rules(self) -> str:
        rules = self.txt_rules.toPlainText().strip()
        if not rules:
            raise ValueError("Please enter at least one display-name rule.")
        return rules

    def fn_refresh_theme(self):
        colors = ThemeManager.fn_colors()

        self.txt_rules.setStyleSheet(
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
