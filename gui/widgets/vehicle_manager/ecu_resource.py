from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QHBoxLayout,
    QFileDialog,
)
from dataclasses import replace
from html import escape
from PySide6.QtCore import Qt, Signal
from core.dll_resource import inspect_dll_resource
from gui.widgets.controls.primary_label import PrimaryLabel

from models.ecu import ECU

from gui.widgets.controls.primary_lineedit import (
    PrimaryLineEdit,
)

from gui.widgets.controls.secondary_button import (
    SecondaryButton,
)


class ECUResourceWidget(QWidget):
    dll_browsed = Signal()

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
        self.lbl_dll_status = PrimaryLabel('DLL not configured.')
        self.lbl_dll_status.setTextFormat(Qt.PlainText)
        self.lbl_dll_status.setWordWrap(True)
        layout.addRow('', self.lbl_dll_status)
        self.btn_dll.clicked.connect(self._browse_dll)
        self.txt_dll.textChanged.connect(self.txt_dll.setToolTip)
        self.txt_dll.editingFinished.connect(self._refresh_dll_metadata)

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
        *,
        dll_metadata=None,
    ):
        resources = ecu.resources or {}
        self._saved_dll_metadata = dll_metadata
        self._browsed_dll = None
        self._saved_dll_value = resources.get('dll','') or ''
        self.txt_dll.setText(
            resources.get(
                "dll",
                "",
            )
        )

        self.txt_odx.setText(
            resources.get(
                "odx",
                "",
            )
        )

        self.txt_dbc.setText(
            resources.get(
                "dbc",
                "",
            )
        )

        self.txt_dtc.setText(
            resources.get(
                "dtc",
                "",
            )
        )

        self.txt_request.setText(
            resources.get(
                "request_library",
                "",
            )
        )
        self._refresh_dll_metadata()

    def fn_get_ecu(
        self,
        ecu: ECU,
    ) -> ECU:

        value = self.txt_dll.text()
        if value != self._saved_dll_value and value.strip():
            metadata = self._refresh_dll_metadata()
            if not metadata.configurable: raise ValueError(metadata.message)
            value = metadata.path
        resources = dict(ecu.resources or {})
        resources.update(dll=value,odx=self.txt_odx.text(),dbc=self.txt_dbc.text(),
                         dtc=self.txt_dtc.text(),request_library=self.txt_request.text())
        return replace(ecu,resources=resources)

    def fn_dll_import_source(self):
        value = self.txt_dll.text()
        if value.strip() and (value != self._saved_dll_value or self._browsed_dll == value):
            return value
        return None

    def _browse_dll(self):
        value,_ = QFileDialog.getOpenFileName(self,'Select ECU DLL','','DLL files (*.dll)')
        if not value: return
        metadata = inspect_dll_resource(value)
        self._show_dll_metadata(metadata)
        if metadata.configurable:
            self.txt_dll.setText(metadata.path)
            self._browsed_dll = metadata.path
            self.dll_browsed.emit()

    def _refresh_dll_metadata(self):
        value = self.txt_dll.text()
        metadata = (self._saved_dll_metadata if value == self._saved_dll_value
                    and self._saved_dll_metadata is not None else inspect_dll_resource(value))
        self._show_dll_metadata(metadata)
        return metadata

    def _show_dll_metadata(self,metadata):
        self.lbl_dll_status.setText(metadata.message)
        self.lbl_dll_status.setToolTip(escape(f'{metadata.machine}; {metadata.bits or "unknown"}-bit\n'
            f'Exports: {", ".join(metadata.exports[:16]) or "none"}\nStatic inspection only; no ABI or execution verified.'))

    def fn_clear(self):
        self._saved_dll_value = ''
        self._saved_dll_metadata = None
        self._browsed_dll = None
        self.txt_dll.clear()

        self.txt_odx.clear()

        self.txt_dbc.clear()

        self.txt_dtc.clear()

        self.txt_request.clear()
        self._refresh_dll_metadata()

    def fn_refresh_theme(self):
        self.lbl_dll_status.fn_refresh_theme()
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
