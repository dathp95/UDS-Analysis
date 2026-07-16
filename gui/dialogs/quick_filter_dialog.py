from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
)

from gui.widgets.controls.primary_button import (
    PrimaryButton
)

from gui.widgets.controls.primary_label import (
    PrimaryLabel
)

from gui.widgets.controls.primary_lineedit import (
    PrimaryLineEdit
)

class QuickFilterDialog(QDialog):

    def __init__(self, quick_filter=None, parent=None):

        super().__init__(parent)

        self.setWindowTitle(
            "Quick Filter"
        )

        self.resize(420, 200)

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

        

        # --------------------------------------
        # Buttons
        # --------------------------------------

        self.button_layout = QHBoxLayout()

        self.button_layout.addStretch()

        self.btn_save = PrimaryButton(
            "Save",
            width=100
        )

        self.btn_cancel = PrimaryButton(
            "Cancel",
            width=100
        )
        

        self.button_layout.addWidget(
            self.btn_save
        )

        self.button_layout.addWidget(
            self.btn_cancel
        )

        self.main_layout.addLayout(
            self.button_layout
        )


        
    
    def _connect_signals(self):

        self.btn_save.clicked.connect(

            self.accept

        )

        self.btn_cancel.clicked.connect(

            self.reject

        )
    
    
    def fn_get_data(self) -> dict:

        data = {

            "name": self.fields["name"].text().strip(),

            "filters": {

                "ecu": self.fields["ecu"].text().strip().upper(),

                "request": self.fields["request"].text().strip().upper()

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

            quick_filter["filters"]["request"]

        )

    def _fn_load_data(self) -> None:
        """
        Load quick filter data into the dialog.
        """

        self.fn_set_data(
            self.quick_filter
        )

        
    