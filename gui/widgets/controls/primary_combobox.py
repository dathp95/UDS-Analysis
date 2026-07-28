from PySide6.QtWidgets import QComboBox

from gui.themes.styles.controls.combobox_style import (
    fn_combobox_style
)


class PrimaryComboBox(QComboBox):

    def __init__(
        self,
        minimum_height: int = 36,
        parent=None,
    ):
        super().__init__(parent)

        self.setMinimumHeight(
            minimum_height
        )


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
            fn_combobox_style()
        )