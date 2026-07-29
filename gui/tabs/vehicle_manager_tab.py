from PySide6.QtWidgets import (
    QGroupBox,
    QScrollArea,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
)

from gui.controllers.vehicle_controller import VehicleController
from gui.themes.styles.containers.groupbox_style import fn_groupbox_style
from gui.themes.styles.controls.scrollbar_style import (
    fn_apply_scrollbar_style,
)
from gui.widgets.controls.primary_button import PrimaryButton

from gui.widgets.vehicle_manager.vehicle_selector import (
    VehicleSelectorWidget,
)

from gui.widgets.vehicle_manager.ecu_list import (
    ECUList,
)


from gui.widgets.vehicle_manager.ecu_info import (
    ECUInfoWidget,
)

from gui.widgets.vehicle_manager.ecu_resource import (
    ECUResourceWidget,
)

class VehicleManagerTab(QWidget):

    def __init__(self):

        super().__init__()
        self._current_vehicle = None

        self._current_ecu = None

        self._create_controller()

        self._setup_ui()

        self._connect_signals()

        self._load_data()

    # ==========================================
    # Private
    # ==========================================

    def _create_controller(self):

        self._controller = VehicleController()

    def _setup_ui(self):

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            16,
            16,
            16,
            16,
        )

        main_layout.setSpacing(12)

        self.vehicle_selector = VehicleSelectorWidget()

        self.vehicle_panel = self._create_panel(
            "Vehicle Package",
            self.vehicle_selector,
        )

        main_layout.addWidget(
            self.vehicle_panel
        )

        content_layout = QHBoxLayout()

        content_layout.setSpacing(12)

        self.ecu_list = ECUList()

        self.ecu_info = ECUInfoWidget()

        self.ecu_resource = ECUResourceWidget()

        self.btn_save = PrimaryButton(
            "Save",
            width=120,
        )

        self.btn_save.setEnabled(False)

        self.ecu_list_panel = self._create_panel(
            "ECU List",
            self.ecu_list,
        )

        self.ecu_info_panel = self._create_panel(
            "Basic Information",
            self.ecu_info,
        )

        self.ecu_resource_panel = self._create_panel(
            "Resources",
            self.ecu_resource,
        )

        detail_widget = QWidget()

        detail_layout = QVBoxLayout(detail_widget)

        detail_layout.setContentsMargins(0, 0, 0, 0)

        detail_layout.setSpacing(12)

        detail_layout.addWidget(
            self.ecu_info_panel
        )

        detail_layout.addWidget(
            self.ecu_resource_panel
        )

        action_layout = QHBoxLayout()

        action_layout.setContentsMargins(0, 0, 0, 0)

        action_layout.addStretch()

        action_layout.addWidget(
            self.btn_save
        )

        detail_layout.addLayout(
            action_layout
        )

        detail_layout.addStretch()

        self.detail_scroll_area = QScrollArea()

        self.detail_scroll_area.setWidgetResizable(True)

        self.detail_scroll_area.setFrameShape(
            QScrollArea.NoFrame
        )

        self.detail_scroll_area.setWidget(
            detail_widget
        )

        fn_apply_scrollbar_style(
            self.detail_scroll_area
        )

        content_layout.addWidget(
            self.ecu_list_panel,
            1,
        )

        content_layout.addWidget(
            self.detail_scroll_area,
            4,
        )

        main_layout.addLayout(
            content_layout
        )

    def _create_panel(
            self,
            title: str,
            widget: QWidget,
        ) -> QGroupBox:

        panel = QGroupBox(title)

        layout = QVBoxLayout(panel)

        layout.setContentsMargins(
            12,
            14,
            12,
            12,
        )

        layout.setSpacing(8)

        layout.addWidget(widget)

        return panel

    def _connect_signals(self):

        self.vehicle_selector.vehicle_changed.connect(

            self._on_vehicle_changed

        )

        self.ecu_list.ecu_selected.connect(

            self._on_ecu_selected

        )

        self.btn_save.clicked.connect(

            self._on_save_clicked

        )

    def _load_data(self):        

        vehicles = self._controller.list_vehicles()

        self.vehicle_selector.fn_set_vehicles(
            vehicles
        )
        if vehicles:

            self._on_vehicle_changed(
                vehicles[0]
            )

    def _on_vehicle_changed(
            self,
            vehicle_name: str,
        ):

        self._current_vehicle = self._controller.load_vehicle(
            vehicle_name
        )

        ecu_names = [

            ecu.name

            for ecu in self._current_vehicle.ecus

        ]

        self.ecu_info.fn_clear()

        self.ecu_resource.fn_clear()

        self._current_ecu = None

        self.btn_save.setEnabled(False)

        self.ecu_list.fn_set_ecus(
            ecu_names
        )

        if ecu_names:

            self._on_ecu_selected(
                ecu_names[0]
            )

    # ==========================================
    # Public
    # ==========================================


    def _on_ecu_selected(
            self,
            ecu_name: str,
        ):

        for ecu in self._current_vehicle.ecus:

            if ecu.name == ecu_name:

                self._current_ecu = ecu

                self.ecu_info.fn_set_ecu(
                    ecu
                )

                self.ecu_resource.fn_set_ecu(
                    ecu
                )

                self.btn_save.setEnabled(True)

                break

    def _on_save_clicked(self):

        if self._current_ecu is None:

            return

        self.ecu_info.fn_get_ecu(

            self._current_ecu

        )

        self.ecu_resource.fn_get_ecu(

            self._current_ecu

        )

        print(self._current_ecu)


    def fn_refresh_theme(self):

        self.setStyleSheet("")

        for panel in (
            self.vehicle_panel,
            self.ecu_list_panel,
            self.ecu_info_panel,
            self.ecu_resource_panel,
        ):

            panel.setStyleSheet(
                fn_groupbox_style()
            )

        fn_apply_scrollbar_style(
            self.detail_scroll_area
        )

        self.vehicle_selector.fn_refresh_theme()

        self.ecu_list.fn_refresh_theme()

        self.ecu_info.fn_refresh_theme()

        self.ecu_resource.fn_refresh_theme()

        self.btn_save.fn_refresh_theme()
