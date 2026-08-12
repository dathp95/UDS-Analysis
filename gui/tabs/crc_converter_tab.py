from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.crc import calculate_crc8_sae_j1850, parse_hex_bytes
from gui.themes.theme_manager import ThemeManager
from gui.themes.styles.controls.scrollbar_style import fn_apply_scrollbar_style
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_label import PrimaryLabel
from gui.widgets.controls.primary_lineedit import PrimaryLineEdit


class CRCConverterTab(QWidget):

    def __init__(self):
        super().__init__()

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
        self.txt_crc_input = QPlainTextEdit()
        self.txt_crc_input.setPlaceholderText("01 02 03 04 05")
        self.txt_crc_input.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.txt_crc_input.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.txt_crc_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._set_editor_three_line_height(self.txt_crc_input, lines =20)

        self.btn_calculate_crc = PrimaryButton(
            "Calculate CRC",
            width=140,
        )
        self.txt_crc_output = PrimaryLineEdit()
        self.txt_crc_output.setReadOnly(True)
        self.txt_crc_output.setFixedWidth(80)

        result_layout = QHBoxLayout()
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_layout.setSpacing(8)
        result_layout.addWidget(self.btn_calculate_crc)
        result_layout.addWidget(self.txt_crc_output)
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
        panel_layout.addWidget(self.lbl_converter)
        panel_layout.addStretch(1)

    def _connect_signals(self):
        self.btn_calculate_crc.clicked.connect(
            self.calculate_crc8_sae_j1850
        )

    @staticmethod
    def _set_editor_three_line_height(editor, lines =3):
        line_height = editor.fontMetrics().lineSpacing()
        frame_width = editor.frameWidth() * 2
        vertical_padding = 12
        height = line_height * lines + frame_width + vertical_padding
        editor.setMinimumHeight(height)
        editor.setMaximumHeight(height)

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

    def fn_refresh_theme(self):
        colors = ThemeManager.fn_colors()

        self.setStyleSheet("")
        self.lbl_crc8_sae_j1850.fn_refresh_theme()
        self.lbl_converter.fn_refresh_theme()
        self.btn_calculate_crc.fn_refresh_theme()
        self.txt_crc_output.fn_refresh_theme()
        self.txt_crc_input.setStyleSheet(
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
        fn_apply_scrollbar_style(self.txt_crc_input)
