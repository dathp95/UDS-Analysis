from PySide6.QtWidgets import QLabel

from gui.themes.styles.controls.label_style import (
    fn_label_style
)


class PrimaryLabel(QLabel):

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
            fn_label_style()
        )