from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMessageBox,
    QHBoxLayout,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.converter import SUPPORTED_FORMATS, convert_data
from core.crc import calculate_crc8_sae_j1850, parse_hex_bytes
from core.qr_generator import QRDependencyError, generate_qr_png_bytes
from gui.themes.theme_manager import ThemeManager
from gui.themes.styles.controls.scrollbar_style import fn_apply_scrollbar_style
from gui.utils.text_selection import clear_text_selection_on_focus_out
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_combobox import PrimaryComboBox
from gui.widgets.controls.primary_label import PrimaryLabel
from gui.widgets.controls.primary_lineedit import PrimaryLineEdit


class CRCConverterTab(QWidget):

    DEFAULT_FROM_FORMAT = "Hexadecimal"
    DEFAULT_TO_FORMAT = "Decimal"
    crc_transfer_requested = Signal(str)

    def __init__(self):
        super().__init__()

        self._generated_qr_pixmap = None
        self._setup_ui()
        self._connect_signals()
        self.fn_refresh_theme()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        self.crc_panel = QWidget()
        self.converter_panel = QWidget()

        self._setup_crc_panel()
        self._setup_converter_panel()

        main_layout.addWidget(self.crc_panel, 1)
        main_layout.addWidget(self.converter_panel, 1)

    def _setup_crc_panel(self):
        panel_layout = QVBoxLayout(self.crc_panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(8)

        self.lbl_crc8_sae_j1850 = PrimaryLabel("CRC8_SAE_J1850")
        self.txt_crc_input = self._create_multiline_editor(
            placeholder="01 02 03 04 05",
            lines=28,
        )

        self.btn_calculate_crc = PrimaryButton(
            "Calculate CRC",
            width=140,
        )
        self.txt_crc_output = PrimaryLineEdit()
        self.txt_crc_output.setReadOnly(True)
        self.txt_crc_output.setFixedWidth(80)
        self.btn_copy_crc = PrimaryButton("COPY CRC", width=100)
        self.btn_copy_crc.setEnabled(False)
        self.btn_transfer_crc = PrimaryButton("Transfer CRC", width=120)
        self.btn_transfer_crc.setEnabled(False)

        result_layout = QHBoxLayout()
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_layout.setSpacing(8)
        result_layout.addWidget(self.btn_calculate_crc)
        result_layout.addWidget(self.txt_crc_output)
        result_layout.addWidget(self.btn_copy_crc)
        result_layout.addWidget(self.btn_transfer_crc)
        result_layout.addStretch(1)

        panel_layout.addWidget(self.lbl_crc8_sae_j1850)
        panel_layout.addWidget(self.txt_crc_input)
        panel_layout.addLayout(result_layout)
        panel_layout.addStretch(1)

    def _setup_converter_panel(self):
        panel_layout = QVBoxLayout(self.converter_panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(8)

        self.lbl_converter = PrimaryLabel("Converter")
        self.lbl_converter_from = PrimaryLabel("From")
        self.lbl_converter_to = PrimaryLabel("To")
        self.cmb_converter_from = self._create_format_combo()
        self.cmb_converter_to = self._create_format_combo()
        self._set_combo_text(self.cmb_converter_from, self.DEFAULT_FROM_FORMAT)
        self._set_combo_text(self.cmb_converter_to, self.DEFAULT_TO_FORMAT)

        format_layout = QHBoxLayout()
        format_layout.setContentsMargins(0, 0, 0, 0)
        format_layout.setSpacing(8)
        format_layout.addLayout(
            self._create_labeled_control_layout(
                self.lbl_converter_from,
                self.cmb_converter_from,
            ),
            1,
        )
        format_layout.addLayout(
            self._create_labeled_control_layout(
                self.lbl_converter_to,
                self.cmb_converter_to,
            ),
            1,
        )

        self.lbl_converter_input = PrimaryLabel("Input")
        self.txt_converter_input = self._create_multiline_editor(
            placeholder="41 42 43",
            lines=8,
        )

        self.lbl_converter_output = PrimaryLabel("Output")
        self.txt_converter_output = self._create_multiline_editor(lines=8)
        self.txt_converter_output.setReadOnly(True)

        editor_layout = QHBoxLayout()
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(8)
        editor_layout.addLayout(
            self._create_labeled_control_layout(
                self.lbl_converter_input,
                self.txt_converter_input,
            ),
            1,
        )
        editor_layout.addLayout(
            self._create_labeled_control_layout(
                self.lbl_converter_output,
                self.txt_converter_output,
            ),
            1,
        )

        self.btn_converter_convert = PrimaryButton("CONVERT", width=100)
        self.btn_converter_swap = PrimaryButton("SWAP", width=100)
        self.btn_converter_clear = PrimaryButton("CLEAR", width=100)
        self.btn_converter_copy = PrimaryButton("Copy Result", width=120)
        self.btn_converter_clear.setEnabled(False)
        self.btn_converter_copy.setEnabled(False)

        left_action_layout = QHBoxLayout()
        left_action_layout.setContentsMargins(0, 0, 0, 0)
        left_action_layout.setSpacing(8)
        left_action_layout.addWidget(self.btn_converter_convert)
        left_action_layout.addWidget(self.btn_converter_swap)
        left_action_layout.addWidget(self.btn_converter_clear)
        left_action_layout.addStretch(1)

        right_action_layout = QHBoxLayout()
        right_action_layout.setContentsMargins(0, 0, 0, 0)
        right_action_layout.setSpacing(8)
        right_action_layout.addWidget(self.btn_converter_copy)
        right_action_layout.addStretch(1)

        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(8)
        action_layout.addLayout(left_action_layout, 1)
        action_layout.addLayout(right_action_layout, 1)

        panel_layout.addWidget(self.lbl_converter)
        panel_layout.addLayout(format_layout)
        panel_layout.addLayout(editor_layout)
        panel_layout.addLayout(action_layout)
        panel_layout.addSpacing(8)
        self._setup_qr_panel(panel_layout)
        panel_layout.addStretch(1)

        self._install_text_selection_handlers()

    def _setup_qr_panel(self, parent_layout):
        # ==========================================================
        # Widgets
        # ==========================================================

        self.lbl_qr_generator = PrimaryLabel(
            "QR Code Generator: Eg: RLNVBL9K8RH722527"
        )
        self.lbl_qr_generator.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        self.txt_qr_input = self._create_multiline_editor(lines=5)

        self.btn_create_qr = PrimaryButton(
            "Create QR",
            width=100,
        )

        self.btn_copy_qr = PrimaryButton(
            "Copy QR",
            width=100,
        )

        self.btn_clear_qr = PrimaryButton(
            "Clear QR",
            width=100,
        )
        self.btn_copy_qr.setEnabled(False)
        self.btn_clear_qr.setEnabled(False)

        # ==========================================================
        # QR Preview
        # ==========================================================

        self.lbl_qr_preview = QLabel()
        self.lbl_qr_preview.setAlignment(Qt.AlignCenter)
        self.lbl_qr_preview.setFixedSize(180, 180)

        # ==========================================================
        # Action Layout
        # ==========================================================

        qr_action_layout = QHBoxLayout()
        qr_action_layout.setContentsMargins(0, 0, 0, 0)
        qr_action_layout.setSpacing(8)

        qr_action_layout.addWidget(self.btn_create_qr)
        qr_action_layout.addWidget(self.btn_copy_qr)
        qr_action_layout.addWidget(self.btn_clear_qr)
        qr_action_layout.addStretch(1)

        # ==========================================================
        # Left: Controls
        # ==========================================================

        qr_control_layout = QVBoxLayout()
        qr_control_layout.setContentsMargins(0, 0, 0, 0)
        qr_control_layout.setSpacing(8)

        qr_control_layout.addWidget(self.lbl_qr_generator)
        qr_control_layout.addWidget(self.txt_qr_input)
        qr_control_layout.addLayout(qr_action_layout)
        qr_control_layout.addStretch(1)

        # ==========================================================
        # Main QR Content
        # ==========================================================

        qr_content_layout = QHBoxLayout()
        qr_content_layout.setContentsMargins(0, 0, 0, 0)
        qr_content_layout.setSpacing(12)

        # Left
        qr_content_layout.addLayout(
            qr_control_layout,
            1,
        )

        # Right
        qr_content_layout.addWidget(
            self.lbl_qr_preview,
            0,
            Qt.AlignTop | Qt.AlignHCenter,
        )

        # ==========================================================
        # Add to Parent
        # ==========================================================

        parent_layout.addLayout(qr_content_layout)

    def _install_text_selection_handlers(self):
        clear_text_selection_on_focus_out(
            self,
            [
                self.txt_crc_input,
                self.txt_crc_output,
                self.txt_converter_input,
                self.txt_converter_output,
                self.txt_qr_input,
            ],
        )

    def _connect_signals(self):
        self.btn_calculate_crc.clicked.connect(
            self.calculate_crc8_sae_j1850
        )
        self.btn_copy_crc.clicked.connect(
            self.copy_crc_result
        )
        self.btn_transfer_crc.clicked.connect(
            self.transfer_crc_result
        )
        self.txt_crc_output.textChanged.connect(
            self._update_crc_button_states
        )
        self.btn_converter_convert.clicked.connect(
            self.convert_value
        )
        self.btn_converter_swap.clicked.connect(
            self.swap_converter_formats
        )
        self.btn_converter_clear.clicked.connect(
            self.clear_converter
        )
        self.btn_converter_copy.clicked.connect(
            self.copy_converter_result
        )
        self.txt_converter_input.textChanged.connect(
            self._update_converter_button_states
        )
        self.txt_converter_output.textChanged.connect(
            self._update_converter_button_states
        )
        self.btn_create_qr.clicked.connect(
            self.create_qr_code
        )
        self.btn_copy_qr.clicked.connect(
            self.copy_qr_code
        )
        self.btn_clear_qr.clicked.connect(
            self.clear_qr_code
        )
        self.txt_qr_input.textChanged.connect(
            self._update_qr_button_states
        )

    def _create_format_combo(self):
        combo = PrimaryComboBox()
        combo.addItems(SUPPORTED_FORMATS)
        combo.setMaxVisibleItems(len(SUPPORTED_FORMATS))
        fn_apply_scrollbar_style(combo.view())
        return combo

    @staticmethod
    def _create_labeled_control_layout(label, control):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(label)
        layout.addWidget(control)
        return layout

    def _create_multiline_editor(self, placeholder="", lines=3):
        editor = QPlainTextEdit()
        editor.setPlaceholderText(placeholder)
        editor.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        editor.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._set_editor_height(editor, lines=lines)
        return editor

    @staticmethod
    def _set_editor_height(editor, lines=3):
        line_height = editor.fontMetrics().lineSpacing()
        frame_width = editor.frameWidth() * 2
        vertical_padding = 12
        height = line_height * lines + frame_width + vertical_padding
        editor.setMinimumHeight(height)
        editor.setMaximumHeight(height)

    @staticmethod
    def _set_combo_text(combo, text):
        index = combo.findText(text)
        if index >= 0:
            combo.setCurrentIndex(index)

    def calculate_crc8_sae_j1850(self):
        try:
            data = parse_hex_bytes(
                self.txt_crc_input.toPlainText()
            )
            crc = calculate_crc8_sae_j1850(data)
        except ValueError as error:
            self.txt_crc_output.clear()
            self.txt_crc_input.setToolTip(str(error))
            return

        self.txt_crc_input.setToolTip("")
        self.txt_crc_output.setText(f"{crc:02X}")

    def _update_crc_button_states(self):
        has_crc = bool(self.txt_crc_output.text().strip())
        self.btn_copy_crc.setEnabled(has_crc)
        self.btn_transfer_crc.setEnabled(has_crc)

    def convert_value(self):
        try:
            result = convert_data(
                self.txt_converter_input.toPlainText(),
                self.cmb_converter_from.currentText(),
                self.cmb_converter_to.currentText(),
            )
        except ValueError as error:
            self.txt_converter_output.clear()
            self.txt_converter_input.setToolTip(str(error))
            self._update_converter_button_states()
            return

        self.txt_converter_input.setToolTip("")
        self.txt_converter_output.setPlainText(result)
        self._update_converter_button_states()

    def swap_converter_formats(self):
        from_format = self.cmb_converter_from.currentText()
        to_format = self.cmb_converter_to.currentText()
        output = self.txt_converter_output.toPlainText()

        self._set_combo_text(self.cmb_converter_from, to_format)
        self._set_combo_text(self.cmb_converter_to, from_format)
        if output:
            self.txt_converter_input.setPlainText(output)
        self.txt_converter_output.clear()
        self.txt_converter_input.setToolTip("")

    def clear_converter(self):
        self._set_combo_text(self.cmb_converter_from, self.DEFAULT_FROM_FORMAT)
        self._set_combo_text(self.cmb_converter_to, self.DEFAULT_TO_FORMAT)
        self.txt_converter_input.clear()
        self.txt_converter_output.clear()
        self.txt_converter_input.setToolTip("")
        self._update_converter_button_states()

    def _update_converter_button_states(self):
        has_input = bool(self.txt_converter_input.toPlainText().strip())
        has_output = bool(self.txt_converter_output.toPlainText().strip())
        self.btn_converter_clear.setEnabled(has_input or has_output)
        self.btn_converter_copy.setEnabled(has_output)

    def create_qr_code(self):
        text = self.txt_qr_input.toPlainText()
        if not text.strip():
            self._clear_qr_preview()
            QMessageBox.warning(
                self,
                "QR Code Generator",
                "Please input text before creating QR.",
            )
            return

        try:
            qr_bytes = generate_qr_png_bytes(text)
        except (ValueError, QRDependencyError) as error:
            self._clear_qr_preview()
            QMessageBox.warning(
                self,
                "QR Code Generator",
                str(error),
            )
            return

        pixmap = QPixmap()
        if not pixmap.loadFromData(qr_bytes, "PNG"):
            self._clear_qr_preview()
            QMessageBox.warning(
                self,
                "QR Code Generator",
                "Cannot render generated QR image.",
            )
            return

        self._set_qr_preview_pixmap(pixmap)

    def _set_qr_preview_pixmap(self, pixmap):
        self._generated_qr_pixmap = pixmap
        self.lbl_qr_preview.setPixmap(
            pixmap.scaled(
                self.lbl_qr_preview.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )
        self._update_qr_button_states()

    def _clear_qr_preview(self):
        self._generated_qr_pixmap = None
        self.lbl_qr_preview.clear()
        self._update_qr_button_states()

    def _update_qr_button_states(self):
        has_input = bool(self.txt_qr_input.toPlainText().strip())
        has_preview = self._generated_qr_pixmap is not None
        self.btn_copy_qr.setEnabled(has_preview)
        self.btn_clear_qr.setEnabled(has_input or has_preview)

    def clear_qr_code(self):
        self.txt_qr_input.clear()
        self._clear_qr_preview()

    def copy_qr_code(self):
        if self._generated_qr_pixmap is None:
            QMessageBox.information(
                self,
                "QR Code Generator",
                "No QR code to copy.",
            )
            return

        QApplication.clipboard().setPixmap(self._generated_qr_pixmap)

    def copy_crc_result(self):
        QApplication.clipboard().setText(self.txt_crc_output.text())

    def transfer_crc_result(self):
        crc_value = self._normalized_crc_output()
        if not crc_value:
            QMessageBox.warning(
                self,
                "Transfer CRC",
                "Please calculate CRC before transferring.",
            )
            return

        self.crc_transfer_requested.emit(crc_value)

    def _normalized_crc_output(self):
        crc_text = self.txt_crc_output.text().strip()
        if not crc_text:
            return ""

        crc_text = crc_text.removeprefix("0x").removeprefix("0X")
        try:
            return f"{int(crc_text, 16):02X}"
        except ValueError:
            return ""
    def copy_converter_result(self):
        QApplication.clipboard().setText(
            self.txt_converter_output.toPlainText()
        )

    def fn_refresh_theme(self):
        colors = ThemeManager.fn_colors()

        self.setStyleSheet("")
        self.lbl_crc8_sae_j1850.fn_refresh_theme()
        self.lbl_converter.fn_refresh_theme()
        self.lbl_converter_from.fn_refresh_theme()
        self.lbl_converter_to.fn_refresh_theme()
        self.lbl_converter_input.fn_refresh_theme()
        self.lbl_converter_output.fn_refresh_theme()
        self.lbl_qr_generator.fn_refresh_theme()
        self.cmb_converter_from.fn_refresh_theme()
        self.cmb_converter_to.fn_refresh_theme()
        self.btn_calculate_crc.fn_refresh_theme()
        self.btn_copy_crc.fn_refresh_theme()
        self.btn_transfer_crc.fn_refresh_theme()
        self.btn_converter_convert.fn_refresh_theme()
        self.btn_converter_swap.fn_refresh_theme()
        self.btn_converter_clear.fn_refresh_theme()
        self.btn_converter_copy.fn_refresh_theme()
        self.btn_create_qr.fn_refresh_theme()
        self.btn_copy_qr.fn_refresh_theme()
        self.btn_clear_qr.fn_refresh_theme()
        self.txt_crc_output.fn_refresh_theme()
        self._refresh_editor_theme(self.txt_crc_input, colors)
        self._refresh_editor_theme(self.txt_converter_input, colors)
        self._refresh_editor_theme(self.txt_converter_output, colors)
        self._refresh_editor_theme(self.txt_qr_input, colors)
        self._refresh_qr_preview_theme(colors)

    def _refresh_qr_preview_theme(self, colors):
        self.lbl_qr_preview.setStyleSheet(
            f"""
            QLabel {{
                background: {colors.WINDOW};
                border: 1px solid {colors.BORDER};
                border-radius: 6px;
            }}
            """
        )

    @staticmethod
    def _refresh_editor_theme(editor, colors):
        editor.setStyleSheet(
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
        fn_apply_scrollbar_style(editor)
