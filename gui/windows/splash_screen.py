from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSplashScreen,
    QVBoxLayout,
    QWidget,
)

from config.paths import IMAGE_DIR


class VCodeSplashScreen(QSplashScreen):
    """
    Modern splash screen for V-CODE application startup with progress indicator.
    Displays brand splash banner and provides responsive visual feedback
    while heavy workspace components and themes are initialized.
    """

    WIDTH = 640
    HEIGHT = 360

    def __init__(self, parent: QWidget | None = None) -> None:
        splash_image_path = IMAGE_DIR / "v_code_splash_screen.png"
        pixmap = self._load_splash_pixmap(splash_image_path)

        super().__init__(pixmap, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        self._setup_ui()

    def _load_splash_pixmap(self, path: Path) -> QPixmap:
        if path.is_file():
            source = QPixmap(str(path))
            if not source.isNull():
                return source.scaled(
                    self.WIDTH,
                    self.HEIGHT,
                    Qt.IgnoreAspectRatio,
                    Qt.SmoothTransformation,
                )

        # Fallback dark brand canvas if image file is not found
        fallback = QPixmap(self.WIDTH, self.HEIGHT)
        fallback.fill(QColor(18, 20, 26))
        painter = QPainter(fallback)
        painter.setPen(QColor(240, 240, 240))
        font = painter.font()
        font.setPointSize(24)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(fallback.rect(), Qt.AlignCenter, "V-CODE DIAGNOSTIC")
        painter.end()
        return fallback

    def _setup_ui(self) -> None:
        banner_height = 44
        self._container = QWidget(self)
        self._container.setGeometry(
            0,
            self.HEIGHT - banner_height,
            self.WIDTH,
            banner_height,
        )
        self._container.setStyleSheet("""
            QWidget {
                background: rgba(15, 17, 23, 0.94);
                border-top: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)

        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(18, 6, 18, 8)
        layout.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        self.lbl_status = QLabel("Initializing V-CODE...")
        self.lbl_status.setStyleSheet("""
            color: #d1d5db;
            font-size: 11px;
            font-weight: 500;
            background: transparent;
        """)

        self.lbl_percent = QLabel("0%")
        self.lbl_percent.setStyleSheet("""
            color: #38bdf8;
            font-size: 11px;
            font-weight: 600;
            background: transparent;
        """)

        top_row.addWidget(self.lbl_status)
        top_row.addStretch()
        top_row.addWidget(self.lbl_percent)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(5)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #27272a;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0284c7, stop:1 #38bdf8
                );
                border-radius: 2px;
            }
        """)

        layout.addLayout(top_row)
        layout.addWidget(self.progress_bar)

    def set_progress(self, value: int, message: str = "") -> None:
        """
        Update progress percentage (0-100) and optional status message.
        Pumps Qt events to ensure immediate rendering on screen.
        """
        clamped = max(0, min(100, int(value)))
        self.progress_bar.setValue(clamped)
        self.lbl_percent.setText(f"{clamped}%")
        if message:
            self.lbl_status.setText(message)
        QApplication.processEvents()

