from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
)

from gui.widgets.coding_value.coding_value_panel import CodingValuePanel


class CodingValueTab(QWidget):

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

        self.coding_value_panel = CodingValuePanel()

        main_layout.addWidget(
            self.coding_value_panel,
            1,
        )

    def fn_set_crc_value(self, crc_value):
        return self.coding_value_panel.fn_set_crc_value(crc_value)

    def fn_refresh_theme(self):
        self.coding_value_panel.fn_refresh_theme()