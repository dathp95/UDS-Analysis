from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QHBoxLayout,
)

from models.ecu import ECU

from gui.widgets.controls.primary_lineedit import PrimaryLineEdit
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.secondary_button import SecondaryButton


class ECUEditorWidget(QWidget):

    save_clicked = Signal()

    def __init__(self):

        super().__init__()

        self._setup_ui()

        self._connect_signals()

        self.fn_clear()

    # ==========================================
    # Private
    # ==========================================

    def _setup_ui(self):

        layout = QFormLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(8)

        # ----------------------------------
        # Basic Information
        # ----------------------------------

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

        # ----------------------------------
        # Resources
        # ----------------------------------

        self.txt_dll, dll_layout = self._create_resource_row()

        self.txt_odx, odx_layout = self._create_resource_row()

        self.txt_dbc, dbc_layout = self._create_resource_row()

        self.txt_dtc, dtc_layout = self._create_resource_row()

        self.txt_request_library, req_layout = self._create_resource_row()

        layout.addRow("DLL", dll_layout)

        layout.addRow("ODX", odx_layout)

        layout.addRow("DBC", dbc_layout)

        layout.addRow("DTC", dtc_layout)

        layout.addRow("Request Library", req_layout)

        # ----------------------------------
        # Save
        # ----------------------------------

        self.btn_save = PrimaryButton(
            "Save",
            width=120,
        )

        layout.addRow(
            "",
            self.btn_save,
        )

    def _create_resource_row(self):

        layout = QHBoxLayout()

        layout.setContentsMargins(0, 0, 0, 0)

        edit = PrimaryLineEdit()

        button = SecondaryButton(
            "Browse"
        )

        layout.addWidget(edit)

        layout.addWidget(button)

        return edit, layout

    def _connect_signals(self):

        self.btn_save.clicked.connect(

            self.save_clicked.emit

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

        self.txt_dll.setText(
            ecu.resources.get("dll", "")
        )

        self.txt_odx.setText(
            ecu.resources.get("odx", "")
        )

        self.txt_dbc.setText(
            ecu.resources.get("dbc", "")
        )

        self.txt_dtc.setText(
            ecu.resources.get("dtc", "")
        )

        self.txt_request_library.setText(
            ecu.resources.get(
                "request_library",
                "",
            )
        )

    def fn_get_ecu(
        self,
        ecu: ECU,
    ) -> ECU:

        ecu.name = self.txt_name.text()

        ecu.request_id = self.txt_request.text()

        ecu.response_id = self.txt_response.text()

        ecu.resources["dll"] = self.txt_dll.text()

        ecu.resources["odx"] = self.txt_odx.text()

        ecu.resources["dbc"] = self.txt_dbc.text()

        ecu.resources["dtc"] = self.txt_dtc.text()

        ecu.resources["request_library"] = (
            self.txt_request_library.text()
        )

        return ecu

    def fn_clear(self):

        self.txt_name.clear()

        self.txt_request.clear()

        self.txt_response.clear()

        self.txt_dll.clear()

        self.txt_odx.clear()

        self.txt_dbc.clear()

        self.txt_dtc.clear()

        self.txt_request_library.clear()

    def fn_refresh_theme(self):

        pass
