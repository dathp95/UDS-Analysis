from PySide6.QtWidgets import QPushButton

from gui.themes.styles.controls.button_style import (
    fn_primary_button_style
)


class PrimaryButton(QPushButton):

    def __init__(
        self,
        text: str ="",
        width: int = 120,
        height: int = 40,
        parent = None
    ):

        super().__init__(text)

        self.setMinimumSize(width, height)


        self._setup_ui()

    # ====================================
    # Private
    # ====================================

    def _setup_ui(self):

        
        self.fn_refresh_theme()

    # ====================================
    # Public API
    # ====================================

    def fn_refresh_theme(self):

        self.setStyleSheet(
            fn_primary_button_style()
        )

    def fn_set_height(
        self,
        height: int
    ):

        self.setMinimumHeight(height)

    def fn_set_width(
        self,
        width: int
    ):

        self.setMinimumWidth(width)

    def fn_set_size(
        self,
        width: int,
        height: int
    ):

        self.setMinimumSize(width, height)

    def fn_enable(
        self,
        enabled: bool = True
    ):

        self.setEnabled(enabled)