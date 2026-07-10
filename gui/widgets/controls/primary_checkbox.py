from PySide6.QtWidgets import QCheckBox

from gui.themes.styles.controls.checkbox_style import (
    fn_checkbox_style
)


class PrimaryCheckBox(QCheckBox):

    def __init__(
        self,
        text="",
        parent=None
    ):

        super().__init__(text, parent)

        self._setup_ui()

    # ==========================================
    # Private
    # ==========================================

    def _setup_ui(self):

        self.fn_refresh_theme()

    # ==========================================
    # Public
    # ==========================================

    def fn_refresh_theme(self):

        self.setStyleSheet(
            fn_checkbox_style()
        )