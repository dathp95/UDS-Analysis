from PySide6.QtWidgets import QPushButton

from gui.themes.styles.controls.button_style import fn_cancel_button_style


class CancelButton(QPushButton):

    def __init__(
        self,
        text: str = "Cancel",
        width: int = 100,
        height: int = 36,
        parent=None,
    ):
        super().__init__(text, parent)
        self.setMinimumSize(width, height)
        self.fn_refresh_theme()

    def fn_refresh_theme(self):
        self.setStyleSheet(fn_cancel_button_style())
