from PySide6.QtCore import (
    Qt,
    Property,
    QPropertyAnimation,
    QEasingCurve,
)

from PySide6.QtGui import (
    QColor,
    QPainter,
)

from PySide6.QtWidgets import (
    QAbstractButton,
)

from gui.themes.theme_manager import ThemeManager


class ToggleSwitch(QAbstractButton):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setCheckable(True)

        self.setCursor(Qt.PointingHandCursor)

        self.setFixedSize(46, 26)

        # Thumb position
        self._offset = 3

        # Animation
        self._animation = QPropertyAnimation(
            self,
            b"offset",
        )

        self._animation.setDuration(180)

        self._animation.setEasingCurve(
            QEasingCurve.OutCubic
        )

        self.toggled.connect(
            self._start_animation
        )

    # ======================================================
    # Paint
    # ======================================================

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        painter.setPen(Qt.NoPen)

        # Track
        colors = ThemeManager.fn_colors()

        track_color = (
            colors.SWITCH_ON
            if self.isChecked()
            else colors.SWITCH_OFF
        )

        painter.setBrush(
            QColor(track_color)
        )

        painter.drawRoundedRect(
            self.rect(),
            13,
            13,
        )

        # Thumb
        painter.setBrush(
            QColor(colors.SWITCH_THUMB)
        )

        painter.drawEllipse(
            int(self._offset),
            3,
            20,
            20,
        )

    # ======================================================
    # Animation
    # ======================================================

    def _start_animation(self, checked):

        start = self._offset

        end = (
            self.width() - 23
            if checked
            else 3
        )

        self._animation.stop()

        self._animation.setStartValue(start)

        self._animation.setEndValue(end)

        self._animation.start()

    # ======================================================
    # Qt Property
    # ======================================================

    def get_offset(self):

        return self._offset

    def set_offset(self, value):

        self._offset = value

        self.update()

    offset = Property(
        float,
        get_offset,
        set_offset,
    )