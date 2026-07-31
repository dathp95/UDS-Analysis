from PySide6.QtCore import Qt
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

        self._setup_ui()


    # ==========================================
    # Private
    # ==========================================

    def _setup_ui(self):

        self.fn_refresh_theme()

        self._force_opaque_background()

    def _force_opaque_background(self):

        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)

        popup_view = self.view()
        popup_view.setAutoFillBackground(True)
        popup_view.setAttribute(Qt.WA_StyledBackground, True)
        popup_view.setAttribute(Qt.WA_OpaquePaintEvent, True)
        popup_view.viewport().setAutoFillBackground(True)
        popup_view.viewport().setAttribute(Qt.WA_StyledBackground, True)
        popup_view.viewport().setAttribute(Qt.WA_OpaquePaintEvent, True)

    # ==========================================
    # Public
    # ==========================================

    def fn_refresh_theme(self):

        self.setStyleSheet(
            fn_combobox_style()
        )

        self._force_opaque_background()
