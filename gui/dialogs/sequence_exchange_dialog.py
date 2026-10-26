from PySide6.QtCore import Qt
from html import escape
from PySide6.QtWidgets import QApplication, QDialog, QHBoxLayout, QPlainTextEdit, QVBoxLayout

from core.sequence_exchange import HEADERS, export_sequence_text, parse_sequence_text
from gui.themes.theme_manager import ThemeManager
from gui.themes.styles.controls.scrollbar_style import fn_apply_scrollbar_style
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.secondary_button import SecondaryButton
from gui.widgets.controls.cancel_button import CancelButton
from gui.widgets.controls.primary_label import PrimaryLabel
from gui.widgets.controls.primary_combobox import PrimaryComboBox


class SequenceExchangeDialog(QDialog):
    """Explicit preview/apply boundary, or complete clipboard-only export."""
    def __init__(self, parent=None, *, text=None, ecu_names=None):
        super().__init__(parent)
        self.exporting = text is not None
        self.ecu_names = ecu_names
        self.parsed = None
        self.mode = None
        self.setWindowTitle('Export SEQ' if self.exporting else 'Import SEQ')
        self.resize(900, 600)
        layout = QVBoxLayout(self)
        self.instructions = PrimaryLabel(' | '.join(HEADERS))
        self.instructions.setWordWrap(True)
        layout.addWidget(self.instructions)
        self.editor = QPlainTextEdit()
        self.editor.setReadOnly(self.exporting)
        self.editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        layout.addWidget(self.editor, 1)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.preview.setVisible(not self.exporting)
        layout.addWidget(self.preview, 1)
        self.status = PrimaryLabel('')
        self.status.setTextFormat(Qt.PlainText)
        self.status.setMaximumHeight(40)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        row = QHBoxLayout()
        self.mode_combo = PrimaryComboBox(minimum_height=30)
        self.mode_combo.addItems(('Choose Append or Replace', 'Append', 'Replace'))
        self.mode_combo.setVisible(not self.exporting)
        row.addWidget(self.mode_combo)
        self.btn_preview = SecondaryButton('Preview', width=90, height=30)
        self.btn_preview.setVisible(not self.exporting)
        row.addWidget(self.btn_preview)
        row.addStretch()
        self.btn_cancel = CancelButton('Cancel', width=90, height=30)
        self.btn_apply = PrimaryButton('Copy' if self.exporting else 'Apply', width=90, height=30)
        row.addWidget(self.btn_cancel)
        row.addWidget(self.btn_apply)
        layout.addLayout(row)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_apply.clicked.connect(self._apply)
        self.btn_preview.clicked.connect(self._preview)
        self.mode_combo.currentIndexChanged.connect(self._enable_apply)
        self.editor.textChanged.connect(self._invalidate)
        if self.exporting:
            self.editor.setPlainText(text)
        self._enable_apply()
        self.fn_refresh_theme()

    def _invalidate(self):
        self.parsed = None
        self.preview.clear()
        self._enable_apply()

    def _enable_apply(self, *_):
        self.btn_apply.setEnabled(self.exporting or (self.parsed is not None and self.mode_combo.currentIndex() in (1, 2)))

    def _preview(self):
        try:
            self.parsed = parse_sequence_text(self.editor.toPlainText(), ecu_names=self.ecu_names)
        except ValueError as error:
            self.parsed = None
            self.preview.clear()
            self.status.setText(str(error))
        else:
            self.preview.setPlainText(export_sequence_text(self.parsed.steps))
            self.status.setText(f'{len(self.parsed.steps)} rows; positions will be renumbered in source order.\n' + '\n'.join(self.parsed.diagnostics))
        self.status.setToolTip(escape(self.status.text()))
        self._enable_apply()

    def _apply(self):
        if self.exporting:
            QApplication.clipboard().setText(self.editor.toPlainText())
        elif self.parsed is None or self.mode_combo.currentIndex() not in (1, 2):
            return
        else:
            self.mode = 'append' if self.mode_combo.currentIndex() == 1 else 'replace'
        self.accept()

    def fn_refresh_theme(self):
        colors = ThemeManager.fn_colors()
        self.setStyleSheet(f'QDialog {{ background: {colors.WINDOW}; color: {colors.TEXT}; }}')
        for editor in (self.editor, self.preview):
            editor.setStyleSheet(f'QPlainTextEdit {{ background: {colors.WINDOW}; color: {colors.TEXT}; border: 1px solid {colors.BORDER}; border-radius: 6px; padding: 8px; font-family: Consolas; }}')
            fn_apply_scrollbar_style(editor)
        for widget in (self.instructions, self.status, self.mode_combo, self.btn_preview, self.btn_cancel, self.btn_apply):
            widget.fn_refresh_theme()
