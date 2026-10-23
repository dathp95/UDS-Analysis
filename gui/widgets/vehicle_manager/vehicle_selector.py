from PySide6.QtCore import Signal, Qt

from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from gui.widgets.controls.primary_label import PrimaryLabel
from gui.widgets.controls.primary_combobox import PrimaryComboBox

from gui.themes.styles.controls.scrollbar_style import fn_apply_scrollbar_style

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

    def __init__(self, orientation: str = "vertical"):

        super().__init__()

        self._orientation = orientation

        self._setup_ui()

        self._connect_signals()

    # ==========================================
    # Private
    # ==========================================

    def _setup_ui(self):

        layout = self._create_layout()

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.lbl_vehicle = PrimaryLabel("Vehicle")

        self.cmb_vehicle = PrimaryComboBox()

        # Limit the number of visible items
        self.cmb_vehicle.setMaxVisibleItems(10)

        # Apply scrollbar style
        fn_apply_scrollbar_style(self.cmb_vehicle.view())

        self.cmb_vehicle.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.cmb_vehicle.setAutoFillBackground(False)

        layout.addWidget(self.lbl_vehicle)

        layout.addWidget(self.cmb_vehicle)

    def _create_layout(self):

        if self._orientation == "horizontal":

            return QHBoxLayout(self)

        return QVBoxLayout(self)

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

        # Refresh scrollbar style when switching Light/Dark Theme
        fn_apply_scrollbar_style(self.cmb_vehicle.view())
