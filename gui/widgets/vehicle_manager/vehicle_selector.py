from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
)

from gui.widgets.controls.primary_label import PrimaryLabel
from gui.widgets.controls.primary_combobox import PrimaryComboBox


class VehicleSelectorWidget(QWidget):
    """
    Vehicle package selector.

    Displays all available Vehicle Packages and emits
    a signal when the selected vehicle changes.
    """

    # ==========================================
    # Signal
    # ==========================================

    vehicle_changed = Signal(str)

    # ==========================================
    # Constructor
    # ==========================================

    def __init__(self):

        super().__init__()

        self._setup_ui()

        self._connect_signals()

    # ==========================================
    # Private
    # ==========================================

    def _setup_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.lbl_vehicle = PrimaryLabel("Vehicle")

        self.cmb_vehicle = PrimaryComboBox()

        layout.addWidget(self.lbl_vehicle)

        layout.addWidget(self.cmb_vehicle)

    def _connect_signals(self):

        self.cmb_vehicle.currentTextChanged.connect(

            self.vehicle_changed.emit

        )

    # ==========================================
    # Public
    # ==========================================

    def fn_set_vehicles(
        self,
        vehicles: list[str],
        selected_vehicle: str = "",
        allow_empty_selection: bool = False,
    ):

        self.cmb_vehicle.blockSignals(True)

        self.cmb_vehicle.clear()

        self.cmb_vehicle.addItems(
            vehicles
        )

        if selected_vehicle:

            index = self.cmb_vehicle.findText(
                selected_vehicle
            )

            if index >= 0:

                self.cmb_vehicle.setCurrentIndex(
                    index
                )

        elif allow_empty_selection:

            self.cmb_vehicle.setCurrentIndex(-1)

        self.cmb_vehicle.blockSignals(False)

    def fn_vehicle(self) -> str:

        return self.cmb_vehicle.currentText()

    def fn_set_vehicle(
        self,
        vehicle: str,
    ):

        index = self.cmb_vehicle.findText(
            vehicle
        )

        if index >= 0:

            self.cmb_vehicle.setCurrentIndex(
                index
            )

    def fn_refresh_theme(self):

        self.lbl_vehicle.fn_refresh_theme()

        self.cmb_vehicle.fn_refresh_theme()
