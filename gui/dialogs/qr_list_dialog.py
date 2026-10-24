from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QFileDialog, QHBoxLayout, QMessageBox, QPlainTextEdit, QVBoxLayout,
)

from core.qr_excel_export import LIMIT_MESSAGE, MAX_QR_CODES, export_qr_codes_to_excel, parse_qr_codes
from gui.themes.styles.controls.scrollbar_style import fn_apply_scrollbar_style
from gui.themes.theme_manager import ThemeManager
from gui.widgets.controls.action_button import ActionButton
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_label import PrimaryLabel


class QRListDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._exporting = False
        self.setWindowTitle("Import List QR Code")
        self.resize(520, 450)
        self.setMinimumSize(420, 320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        self.lbl_prompt = PrimaryLabel("Enter one QR code per line:")
        layout.addWidget(self.lbl_prompt)
        self.txt_codes = QPlainTextEdit()
        self.txt_codes.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.txt_codes.setAccessibleName("QR code list")
        layout.addWidget(self.txt_codes, 1)
        self.lbl_count = PrimaryLabel()
        layout.addWidget(self.lbl_count)
        self.lbl_limit_warning = PrimaryLabel(LIMIT_MESSAGE)
        self.lbl_limit_warning.setWordWrap(True)
        layout.addWidget(self.lbl_limit_warning)
        actions = QHBoxLayout()
        actions.setSpacing(8)
        actions.addStretch()
        self.btn_create = PrimaryButton("Create Excel", width=130, height=36)
        self.btn_cancel = ActionButton("Cancel", width=100, height=36)
        actions.addWidget(self.btn_create)
        actions.addWidget(self.btn_cancel)
        layout.addLayout(actions)

        self.txt_codes.textChanged.connect(self._refresh_input_state)
        self.btn_create.clicked.connect(self.create_excel)
        self.btn_cancel.clicked.connect(self.reject)
        self.fn_refresh_theme()

    def _refresh_input_state(self):
        count = len(parse_qr_codes(self.txt_codes.toPlainText()))
        self.lbl_count.setText(f"Total QR Codes: {count} / {MAX_QR_CODES}")
        self.lbl_limit_warning.setVisible(count > MAX_QR_CODES)
        self.btn_create.setEnabled(not self._exporting and 1 <= count <= MAX_QR_CODES)

    def create_excel(self):
        if self._exporting:
            return
        codes = parse_qr_codes(self.txt_codes.toPlainText())
        if not 1 <= len(codes) <= MAX_QR_CODES:
            message = LIMIT_MESSAGE if codes else "Enter at least one QR code."
            QMessageBox.warning(self, "QR Code Excel Export", message)
            return

        self._exporting = True
        self._refresh_input_state()
        self.txt_codes.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        try:
            default_name = datetime.now().strftime("QR_Code_List_%Y%m%d_%H%M%S.xlsx")
            filename, _ = QFileDialog.getSaveFileName(
                self, "Create QR Code Excel", default_name, "Excel Workbook (*.xlsx)"
            )
            if not filename:
                return
            output = Path(filename)
            if not output.suffix:
                output = output.with_suffix(".xlsx")
            result = export_qr_codes_to_excel(codes, output)
        except Exception as error:
            message = str(error) or "Cannot export these QR codes. Check the QR content and output file."
            QMessageBox.warning(self, "QR Code Excel Export", message)
            return
        finally:
            self._exporting = False
            self.txt_codes.setEnabled(True)
            self.btn_cancel.setEnabled(True)
            self._refresh_input_state()

        QMessageBox.information(
            self, "QR Code Excel Export",
            "QR Code Excel Export Completed.\n\n"
            f"Total QR Codes: {result.code_count}\nTotal Sheets: {result.sheet_count}",
        )

    def fn_refresh_theme(self):
        colors = ThemeManager.fn_colors()
        self.setStyleSheet(f"QDialog {{ background: {colors.PANEL}; color: {colors.TEXT}; }}")
        self.txt_codes.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {colors.WINDOW};
                color: {colors.TEXT};
                border: 1px solid {colors.BORDER};
                border-radius: 4px;
                padding: 8px;
                font-family: Consolas;
                font-size: 10pt;
            }}
        """)
        fn_apply_scrollbar_style(self.txt_codes)
        self.lbl_prompt.fn_refresh_theme()
        self.lbl_count.fn_refresh_theme()
        self.lbl_limit_warning.setStyleSheet(f"color: {colors.DANGER};")
        self.btn_create.fn_refresh_theme()
        self.btn_cancel.fn_refresh_theme()
        self._refresh_input_state()
