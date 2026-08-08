from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QMessageBox,
)
from PySide6.QtCore import QEvent, Qt

from gui.widgets.controls.primary_button import (
    PrimaryButton
)
from gui.widgets.controls.cancel_button import CancelButton

from gui.widgets.controls.primary_label import (
    PrimaryLabel
)

from gui.widgets.controls.primary_lineedit import (
    PrimaryLineEdit
)
from gui.utils.payload_format import delete_payload_character_at_cursor
from gui.utils.payload_format import format_payload_input
from gui.utils.payload_format import format_payload_input_with_cursor

class QuickFilterDialog(QDialog):

    def __init__(self, quick_filter=None, parent=None):

        super().__init__(parent)

        self.setWindowTitle(
            "Quick Filter"
        )

        self.resize(420, 250)

        self.quick_filter = quick_filter


        self.setup_ui()

        self._connect_signals()

        if self.quick_filter is not None:

            self._fn_load_data()
    
    def setup_ui(self):

        self.main_layout = QVBoxLayout(self)

        self.form_layout = QFormLayout()

        self.main_layout.addLayout(
            self.form_layout
        )

        self.fields = {

            "name": PrimaryLineEdit(
                "Filter Name"
            ),

            "ecu": PrimaryLineEdit(
                "ECU"
            ),

            "request": PrimaryLineEdit(
                "XX XX .. .."
            ),

            "response": PrimaryLineEdit(
                "XX XX .. .."
            ),

        }

        self.form_layout.addRow(

            PrimaryLabel("Name"),

            self.fields["name"]

        )

        self.form_layout.addRow(

            PrimaryLabel("ECU"),

            self.fields["ecu"]

        )

        self.form_layout.addRow(

            PrimaryLabel("Request"),

            self.fields["request"]

        )

        self.form_layout.addRow(
            PrimaryLabel("Response"),
            self.fields["response"]
        )

        # --------------------------------------
        # Buttons
        # --------------------------------------

        self.button_layout = QHBoxLayout()

        self.button_layout.addStretch()

        self.btn_save = PrimaryButton(
            "Save",
            width=100
        )

        self.btn_cancel = CancelButton(
            "Cancel",
            width=100
        )
        

        self.button_layout.addWidget(
            self.btn_cancel
        )

        self.button_layout.addWidget(
            self.btn_save
        )

        self.main_layout.addLayout(
            self.button_layout
        )


        
    
    def _connect_signals(self):

        self.fields["request"].textEdited.connect(
            self._format_request
        )
        self.fields["response"].textEdited.connect(
            self._format_response
        )
        for field in self.fields.values():
            field.installEventFilter(self)

        self.btn_save.clicked.connect(

            self.accept

        )

        self.btn_cancel.clicked.connect(

            self.reject

        )

    def _on_enter_pressed(self):
        has_data = any(
            field.text().strip()
            for field in self.fields.values()
        )
        if not has_data:
            QMessageBox.warning(
                self,
                "Quick Filter",
                "Please enter quick access data before saving.",
            )
            return
        self.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._on_enter_pressed()
            event.accept()
            return
        super().keyPressEvent(event)

    def eventFilter(self, watched, event):
        if watched in self.fields.values() and event.type() == QEvent.KeyPress:
            if (
                    watched in (self.fields["request"], self.fields["response"])
                    and event.key() == Qt.Key_Delete
                    and not watched.hasSelectedText()
                ):
                formatted, cursor = delete_payload_character_at_cursor(
                    watched.text(),
                    watched.cursorPosition(),
                )
                if formatted != watched.text():
                    watched.blockSignals(True)
                    watched.setText(formatted)
                    watched.setCursorPosition(cursor)
                    watched.blockSignals(False)
                    return True

            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self._on_enter_pressed()
                return True
        return super().eventFilter(watched, event)

    def _format_request(self, value):
        self._format_payload_field("request", value)

    def _format_response(self, value):
        self._format_payload_field("response", value)

    def _format_payload_field(self, field_name, value):
        field = self.fields[field_name]
        formatted, cursor = format_payload_input_with_cursor(
            value,
            field.cursorPosition(),
        )
        if formatted != value:
            field.blockSignals(True)
            field.setText(formatted)
            field.setCursorPosition(cursor)
            field.blockSignals(False)
    
    
    def fn_get_data(self) -> dict:

        data = {

            "name": self.fields["name"].text().strip(),

            "filters": {

                "ecu": self.fields["ecu"].text().strip().upper(),

                "request": format_payload_input(
                    self.fields["request"].text().strip()
                ),

                "response": format_payload_input(
                    self.fields["response"].text().strip()
                ),

            }

        }

        if self.quick_filter is not None:

            data["id"] = self.quick_filter["id"]

            data["enabled"] = self.quick_filter["enabled"]

        return data

    def fn_set_data(
            self,
            quick_filter: dict,
        ) -> None:
        """
        Display quick filter data.
        """

        self.fields["name"].setText(

            quick_filter["name"]

        )

        self.fields["ecu"].setText(

            quick_filter["filters"]["ecu"]

        )

        self.fields["request"].setText(

            format_payload_input(
                quick_filter["filters"]["request"]
            )

        )

        self.fields["response"].setText(
            format_payload_input(
                quick_filter.get("filters", {}).get("response", "")
            )
        )

    def _fn_load_data(self) -> None:
        """
        Load quick filter data into the dialog.
        """

        self.fn_set_data(
            self.quick_filter
        )
