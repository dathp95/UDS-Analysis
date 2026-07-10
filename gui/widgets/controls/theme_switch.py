from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QCheckBox,
    QHBoxLayout
)

from gui.themes.theme import ThemeType


class ThemeSwitch(QWidget):

    # ==========================================
    # Signal
    # ==========================================

    theme_changed = Signal(ThemeType)

    # ==========================================
    # Constructor
    # ==========================================

    def __init__(self, parent=None):

        super().__init__(parent)

        self._setup_ui()

        self._connect_signals()

    # ==========================================
    # Private
    # ==========================================

    def _setup_ui(self):

        self.lbl_light = QLabel("☀")

        self.chk_dark = QCheckBox("Dark Mode")

        self.lbl_dark = QLabel("🌙")

        layout = QHBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self.lbl_light)

        layout.addWidget(self.chk_dark)

        layout.addWidget(self.lbl_dark)

        layout.addStretch()

    def _connect_signals(self):

        self.chk_dark.toggled.connect(

            self._on_theme_changed

        )

    def _on_theme_changed(

        self,

        checked: bool

    ):

        if checked:

            self.theme_changed.emit(

                ThemeType.DARK

            )

        else:

            self.theme_changed.emit(

                ThemeType.LIGHT

            )

    # ==========================================
    # Public API
    # ==========================================

    def fn_theme(self) -> ThemeType:

        if self.chk_dark.isChecked():

            return ThemeType.DARK

        return ThemeType.LIGHT

    def fn_set_theme(

        self,

        theme: ThemeType

    ):

        self.chk_dark.blockSignals(True)

        self.chk_dark.setChecked(

            theme == ThemeType.DARK

        )

        self.chk_dark.blockSignals(False)

    def fn_refresh_theme(self):

        """
        Reserved for future.

        When we have switch_style.py,
        apply stylesheet here.
        """

        pass