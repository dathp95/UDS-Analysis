from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QHBoxLayout,
)

from models.ecu import ECU

from gui.widgets.controls.primary_lineedit import (
    PrimaryLineEdit,
)

from gui.widgets.controls.secondary_button import (
    SecondaryButton,
)


class ECUResourceWidget(QWidget):

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

        self.txt_dll, self.btn_dll = self._create_resource_row()

        self.txt_odx, self.btn_odx = self._create_resource_row()

        self.txt_dbc, self.btn_dbc = self._create_resource_row()

        self.txt_dtc, self.btn_dtc = self._create_resource_row()

        self.txt_request, self.btn_request = self._create_resource_row()

        layout.addRow(
            "DLL",
            self._row_widget(
                self.txt_dll,
                self.btn_dll,
            ),
        )

        layout.addRow(
            "ODX",
            self._row_widget(
                self.txt_odx,
                self.btn_odx,
            ),
        )

        layout.addRow(
            "DBC",
            self._row_widget(
                self.txt_dbc,
                self.btn_dbc,
            ),
        )

        layout.addRow(
            "DTC",
            self._row_widget(
                self.txt_dtc,
                self.btn_dtc,
            ),
        )

        layout.addRow(
            "Request Library",
            self._row_widget(
                self.txt_request,
                self.btn_request,
            ),
        )

    def _create_resource_row(self):

        edit = PrimaryLineEdit()

        button = SecondaryButton(
            "Browse"
        )

        return edit, button

    def _row_widget(
        self,
        edit,
        button,
    ):

        widget = QWidget()

        layout = QHBoxLayout(widget)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(6)

        layout.addWidget(edit)

        layout.addWidget(button)

        return widget

    # ==========================================
    # Public
    # ==========================================

    def fn_set_ecu(
        self,
        ecu: ECU,
    ):

        self.txt_dll.setText(
            ecu.resources.get(
                "dll",
                "",
            )
        )

        self.txt_odx.setText(
            ecu.resources.get(
                "odx",
                "",
            )
        )

        self.txt_dbc.setText(
            ecu.resources.get(
                "dbc",
                "",
            )
        )

        self.txt_dtc.setText(
            ecu.resources.get(
                "dtc",
                "",
            )
        )

        self.txt_request.setText(
            ecu.resources.get(
                "request_library",
                "",
            )
        )

    def fn_get_ecu(
        self,
        ecu: ECU,
    ) -> ECU:

        ecu.resources["dll"] = self.txt_dll.text()

        ecu.resources["odx"] = self.txt_odx.text()

        ecu.resources["dbc"] = self.txt_dbc.text()

        ecu.resources["dtc"] = self.txt_dtc.text()

        ecu.resources["request_library"] = (
            self.txt_request.text()
        )

        return ecu

    def fn_clear(self):

        self.txt_dll.clear()

        self.txt_odx.clear()

        self.txt_dbc.clear()

        self.txt_dtc.clear()

        self.txt_request.clear()

    def fn_refresh_theme(self):

        self.txt_dll.fn_refresh_theme()

        self.txt_odx.fn_refresh_theme()

        self.txt_dbc.fn_refresh_theme()

        self.txt_dtc.fn_refresh_theme()

        self.txt_request.fn_refresh_theme()

        self.btn_dll.fn_refresh_theme()

        self.btn_odx.fn_refresh_theme()

        self.btn_dbc.fn_refresh_theme()

        self.btn_dtc.fn_refresh_theme()

        self.btn_request.fn_refresh_theme()
