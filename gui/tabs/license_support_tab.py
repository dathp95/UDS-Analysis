from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
)


class LicenseSupportTab(QWidget):

    def __init__(self):
        super().__init__()

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            12,
            12,
            12,
            12,
        )
        main_layout.setSpacing(12)

    def fn_refresh_theme(self):
        self.setStyleSheet("")
