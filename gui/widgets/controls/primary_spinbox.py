from PySide6.QtWidgets import QSpinBox

from gui.themes.styles.controls.spinbox_style import (
    fn_spinbox_style,
)


class PrimarySpinBox(QSpinBox):

    def __init__(
        self,
        minimum_height: int = 36,
        parent=None,
    ):
        super().__init__(parent)

        self.setMinimumHeight(
            minimum_height
        )

        self.fn_refresh_theme()

    def fn_refresh_theme(self):

        self.setStyleSheet(
            fn_spinbox_style()
        )
