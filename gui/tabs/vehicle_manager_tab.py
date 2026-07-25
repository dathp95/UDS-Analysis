from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)


class VehicleManagerTab(QWidget):

    def __init__(self):
        super().__init__()

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.lbl_placeholder = QLabel(
            "Vehicle Manager"
        )

        layout.addWidget(
            self.lbl_placeholder
        )
        layout.addStretch()

    def fn_refresh_theme(self):
        pass
