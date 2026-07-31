from PySide6.QtWidgets import QDialog, QHBoxLayout, QMessageBox, QPlainTextEdit, QVBoxLayout

from gui.themes.theme_manager import ThemeManager
from gui.widgets.controls.cancel_button import CancelButton
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_label import PrimaryLabel
from gui.utils.payload_format import format_payload_input


class ImportQuickFiltersDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Quick Access Filters")
        self.resize(620, 440)
        layout = QVBoxLayout(self)
        layout.addWidget(PrimaryLabel("Format: Name|ECU|Request|Response"))
        layout.addWidget(PrimaryLabel("Example: Read VIN MHU |MHU|22 F1 90|62 F1 90 xx xx .."))
        self.txt_filters = QPlainTextEdit()
        self.txt_filters.setPlaceholderText(
            "Read VIN MHU |MHU|22 F1 90|62 F1 12\nWrite VIN BCM|BCM|2E F1 90|6E F1 90 xx xx .."
        )
        layout.addWidget(self.txt_filters, 1)
        buttons = QHBoxLayout()
        buttons.addStretch()
        self.btn_cancel = CancelButton("Cancel", width=100)
        self.btn_import = PrimaryButton("Import", width=100)
        buttons.addWidget(self.btn_cancel)
        buttons.addWidget(self.btn_import)
        layout.addLayout(buttons)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_import.clicked.connect(self._on_import)
        self.fn_refresh_theme()

    def _on_import(self):
        try:
            self.fn_filters()
        except ValueError as error:
            QMessageBox.warning(self, "Import Quick Access", str(error))
            return
        self.accept()

    def fn_filters(self):
        result = []
        seen = set()
        lines = [line.strip() for line in self.txt_filters.toPlainText().splitlines() if line.strip()]
        if not lines:
            raise ValueError("Please paste at least one quick access filter.")
        for number, line in enumerate(lines, 1):
            parts = [part.strip() for part in line.split("|", 3)]
            if len(parts) != 4 or not parts[0]:
                raise ValueError(f"Line {number} must use Name|ECU|Request|Response.")
            name, ecu, request, response = parts
            if name.casefold() in seen:
                raise ValueError(f"Duplicate quick access name: {name}.")
            seen.add(name.casefold())
            result.append({
                "name": name,
                "filters": {
                    "ecu": ecu.upper(),
                    "request": format_payload_input(request),
                    "response": format_payload_input(response),
                },
            })
        return result

    def fn_refresh_theme(self):
        colors = ThemeManager.fn_colors()
        self.txt_filters.setStyleSheet(
            f"QPlainTextEdit {{ background: {colors.WINDOW}; color: {colors.TEXT}; }}"
        )
        self.btn_cancel.fn_refresh_theme()
        self.btn_import.fn_refresh_theme()
