from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
)

from gui.controllers.vehicle_controller import VehicleController

from gui.widgets.vehicle_manager.vehicle_selector import (
    VehicleSelectorWidget,
)

from gui.widgets.vehicle_manager.ecu_list import (
    ECUList,
)


class VehicleManagerTab(QWidget):

    def __init__(self):

        super().__init__()

        self._create_controller()

        self._setup_ui()

        self._connect_signals()

        self._load_data()

    # ==========================================
    # Private
    # ==========================================

    def _create_controller(self):

        self.controller = VehicleController()

    def _setup_ui(self):

        layout = QVBoxLayout(self)

        self.vehicle_selector = VehicleSelectorWidget()

        self.ecu_list = ECUList()

        layout.addWidget(
            self.vehicle_selector
        )

        layout.addWidget(
            self.ecu_list
        )

        layout.addStretch()

    def _connect_signals(self):

        self.vehicle_selector.vehicle_changed.connect(

            self._on_vehicle_changed

        )

    def _load_data(self):

        vehicles = self.controller.list_vehicles()

        self.vehicle_selector.fn_set_vehicles(
            vehicles
        )

    def _on_vehicle_changed(
        self,
        vehicle_name: str,
    ):

        vehicle = self.controller.load_vehicle(
            vehicle_name
        )

        ecu_names = [

            ecu.name

            for ecu in vehicle.ecus

        ]

        self.ecu_list.fn_set_ecus(
            ecu_names
        )

    # ==========================================
    # Public
    # ==========================================

    def fn_refresh_theme(self):

        self.vehicle_selector.fn_refresh_theme()

        self.ecu_list.fn_refresh_theme()