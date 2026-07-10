from PySide6.QtWidgets import QLineEdit

from gui.themes.styles.controls.lineedit_style import (
    fn_lineedit_style
)


class PrimaryLineEdit(QLineEdit):

    def __init__(
        self,
        placeholder="",
        parent=None
    ):

        super().__init__(parent)

        self.setPlaceholderText(
            placeholder
        )

        self.fn_refresh_theme()

    def fn_refresh_theme(self):

        self.setStyleSheet(
            fn_lineedit_style()
        )