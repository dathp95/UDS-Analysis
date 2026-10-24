from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QProgressBar

from gui.themes.theme_manager import ThemeManager


class QCurrentProgressBar(QProgressBar):
    def __init__(self):
        super().__init__()
        self.setObjectName("analysis_progress_bar")
        self.setFixedSize(315, 36)
        self.setAlignment(Qt.AlignCenter)
        self.set_status("NOT RUN")

    def set_status(self, text):
        self.state = str(text).strip().upper()
        busy = self.state in {"IMPORTING", "ANALYZING"}
        self.setRange(0, 0 if busy else 100)
        self.setValue(100 if self.state in {"IMPORTED", "PASSED", "FAILED"} else 0)
        self.setFormat(self.state + "..." if busy else self.state)
        self.setTextVisible(not busy)
        self.fn_refresh_theme()

    def paintEvent(self, event):
        super().paintEvent(event)
        # Native Qt styles omit the label in indeterminate mode.
        if self.maximum() == 0:
            painter = QPainter(self)
            painter.setPen(QColor(ThemeManager.fn_colors().TEXT))
            painter.drawText(self.rect(), Qt.AlignCenter, self.format())

    def fn_refresh_theme(self):
        colors = ThemeManager.fn_colors()
        state_color = (
            colors.SUCCESS if self.state == "PASSED" else
            colors.DANGER if self.state in {"FAILED", "IMPORT FAILED", "ANALYSIS ERROR"} else
            colors.PRIMARY if self.state in {"IMPORTING", "ANALYZING", "IMPORTED"} else
            colors.BORDER
        )
        text_color = colors.TEXT
        if self.value() == 100:
            fill = QColor(state_color)
            brightness = (fill.red() * 299 + fill.green() * 587 + fill.blue() * 114) / 1000
            dark_text = colors.TEXT if QColor(colors.TEXT).lightnessF() < 0.5 else colors.WINDOW
            text_color = dark_text if brightness > 128 else colors.TEXT_INVERT
        elif self.state in {"IMPORT FAILED", "ANALYSIS ERROR"}:
            text_color = colors.DANGER
        weight = 700 if self.state in {"PASSED", "FAILED"} else 400
        # Match Log Analyzer's progress track, border and chunk geometry.
        self.setStyleSheet(f"""
            QProgressBar {{
                background: {colors.WINDOW};
                color: {text_color};
                font-weight: {weight};
                border: 1px solid {colors.BORDER};
                border-radius: 4px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: {state_color};
                border-radius: 3px;
            }}
        """)
