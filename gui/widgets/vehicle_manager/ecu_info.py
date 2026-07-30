from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
)

from models.ecu import ECU

from gui.widgets.controls.primary_lineedit import (
    PrimaryLineEdit,
)


class ECUInfoWidget(QWidget):
    """
    ECU basic information editor.

    Responsibility:
        - Display ECU basic information.
        - Update ECU object.
    """

    def __init__(self):

        super().__init__()

        self._setup_ui()

        self.fn_clear()

    # ==========================================
    # Private
    # ==========================================

    def _setup_ui(self):

        layout = QFormLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(8)

        self.txt_name = PrimaryLineEdit()

        self.txt_request = PrimaryLineEdit()

        self.txt_response = PrimaryLineEdit()

        layout.addRow(
            "Name",
            self.txt_name,
        )

        layout.addRow(
            "Request ID",
            self.txt_request,
        )

        layout.addRow(
            "Response ID",
            self.txt_response,
        )

    # ==========================================
    # Public
    # ==========================================

    def fn_set_ecu(
        self,
        ecu: ECU,
    ):

        self.txt_name.setText(
            ecu.name
        )

        self.txt_request.setText(
            ecu.request_id
        )

        self.txt_response.setText(
            ecu.response_id
        )

    def fn_get_ecu(
        self,
        ecu: ECU,
    ) -> ECU:

        ecu.name = self.txt_name.text()

        ecu.request_id = self.txt_request.text()

        ecu.response_id = self.txt_response.text()

        return ecu

    def fn_clear(self):

        self.txt_name.clear()

        self.txt_request.clear()

        self.txt_response.clear()

    def fn_refresh_theme(self):

        self.txt_name.fn_refresh_theme()

        self.txt_request.fn_refresh_theme()

        self.txt_response.fn_refresh_theme()
