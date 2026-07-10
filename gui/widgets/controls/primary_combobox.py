from PySide6.QtWidgets import QComboBox

from gui.themes.styles.controls.combobox_style import (
    fn_combobox_style
)


class PrimaryComboBox(QComboBox):

    def __init__(self, parent=None):

        super().__init__(parent)

        self._setup_ui()

    # ==========================================
    # Private
    # ==========================================

    def _setup_ui(self):

        self.setMinimumHeight(36)

        self.fn_refresh_theme()

    # ==========================================
    # Public
    # ==========================================

    def fn_refresh_theme(self):

        self.setStyleSheet(
            fn_combobox_style()
        )