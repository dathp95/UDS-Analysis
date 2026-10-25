from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from gui.themes.theme_manager import ThemeManager
from gui.themes.styles.controls.scrollbar_style import fn_apply_scrollbar_style
from gui.widgets.diagnostic import (
    DiagnosticSequenceList,
    DiagnosticSequenceTable,
)
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_combobox import PrimaryComboBox
from gui.widgets.controls.primary_label import PrimaryLabel
from gui.workers.can_discovery_worker import CANDiscoveryTask
from gui.workers.can_connection_worker import CANConnectionOperation as Operation, CANConnectionTask
from services.can import CANChannelInfo, CANConfig, CANDeviceInfo, CANNoChannelsError, CANService, CANValidationError
from services.can import CANConnectionState as State


class CANInterfaceTab(QWidget):

    BITRATES = (
        (125000, "125 kbit/s"),
        (250000, "250 kbit/s"),
        (500000, "500 kbit/s"),
        (1000000, "1000 kbit/s"),
    )

    def __init__(self, service=None):
        super().__init__()

        self._service = service if service is not None else CANService()
        self._status_state = "Disconnected"
        self._status_message = ""
        self._refreshing = False
        self._closing = False
        self._previous_device = None
        self._previous_channel = None
        app = QApplication.instance()
        self._discovery_task = CANDiscoveryTask(self._service, app)
        self._discovery_task.completed.connect(self._discovery_completed)
        self._discovery_task.failed.connect(self._discovery_failed)
        self.destroyed.connect(self._discovery_task.dispose)
        app.aboutToQuit.connect(self._discovery_task.shutdown)
        self._connection_task = CANConnectionTask(self._service, app)
        self._connection_task.completed.connect(self._connection_completed)
        self._connection_task.failed.connect(self._connection_failed)
        self.destroyed.connect(self._connection_task.dispose)
        app.aboutToQuit.connect(self._connection_task.shutdown)

        self._setup_ui()
        self._connect_signals()
        self._set_status("Disconnected")
        self.fn_refresh_theme()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # Labels
        self.lbl_vendor = PrimaryLabel("Vendor")
        self.lbl_device = PrimaryLabel("Device")
        self.lbl_channel = PrimaryLabel("Channel")
        self.lbl_baudrate = PrimaryLabel("Baudrate")

        # ComboBoxes
        self.cmb_vendor = self._create_vendor_combo()
        self.cmb_device = self._create_device_combo()
        self.cmb_channel = self._create_channel_combo()
        self.cmb_baudrate = self._create_baudrate_combo()

        # Buttons
        self.btn_refresh = PrimaryButton(
            "Refresh",
            width=100,
        )
        self.btn_connect = PrimaryButton(
            "Connect",
            width=100,
        )
        self.btn_disconnect = PrimaryButton(
            "Disconnect",
            width=120,
        )

        # Status
        self.lbl_status = QLabel()
        self.lbl_status.setAlignment(
            Qt.AlignVCenter | Qt.AlignLeft
        )
        self.lbl_status.setMinimumHeight(
            self.btn_connect.minimumHeight()
        )
        self.lbl_status.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed,
        )

        # ==========================================================
        # Config + Actions + Status - Same Row
        # ==========================================================
        # ==========================================================
        # Main Config Row
        # Left = 2/3
        # Right = 1/3
        # ==========================================================

        config_layout = QHBoxLayout()
        config_layout.setContentsMargins(0, 0, 0, 0)
        config_layout.setSpacing(12)


        # ==========================================================
        # LEFT SIDE - Configuration (2/3)
        # ==========================================================

        config_control_layout = QHBoxLayout()
        config_control_layout.setContentsMargins(0, 0, 0, 0)
        config_control_layout.setSpacing(12)

        config_control_layout.addLayout(
            self._create_inline_control(
                self.lbl_vendor,
                self.cmb_vendor,
            ),
            1,
        )

        config_control_layout.addLayout(
            self._create_inline_control(
                self.lbl_device,
                self.cmb_device,
            ),
            1,
        )

        config_control_layout.addLayout(
            self._create_inline_control(
                self.lbl_channel,
                self.cmb_channel,
            ),
            1,
        )

        config_control_layout.addLayout(
            self._create_inline_control(
                self.lbl_baudrate,
                self.cmb_baudrate,
            ),
            1,
        )


        # ==========================================================
        # RIGHT SIDE - Actions + Status (1/3)
        # ==========================================================

        self.action_layout = QHBoxLayout()
        self.action_layout.setContentsMargins(0, 0, 0, 0)
        self.action_layout.setSpacing(8)

        self.action_layout.addWidget(
            self.btn_refresh,
            0,
            Qt.AlignVCenter,
        )

        self.action_layout.addWidget(
            self.btn_connect,
            0,
            Qt.AlignVCenter,
        )

        self.action_layout.addWidget(
            self.btn_disconnect,
            0,
            Qt.AlignVCenter,
        )

        self.action_layout.addWidget(
            self.lbl_status,
            0,
            Qt.AlignVCenter,
        )

        self.action_layout.addStretch(1)


        # ==========================================================
        # Ratio: Configuration 2/3 | Actions 1/3
        # ==========================================================

        config_layout.addLayout(
            config_control_layout,
            2,
        )

        config_layout.addLayout(
            self.action_layout,
            1,
        )

        self.sequence_list = DiagnosticSequenceList()
        self.sequence_table = DiagnosticSequenceTable()
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)
        content_layout.addWidget(self.sequence_list, 1)
        content_layout.addWidget(self.sequence_table, 3)

        main_layout.addLayout(config_layout)
        main_layout.addLayout(content_layout, 1)
        

    def _connect_signals(self):
        self.btn_refresh.clicked.connect(self.refresh_can_setup)
        self.btn_connect.clicked.connect(self.connect_can)
        self.btn_disconnect.clicked.connect(self.disconnect_can)
        self.cmb_device.currentIndexChanged.connect(self._populate_device_channels)
        self.cmb_channel.currentIndexChanged.connect(self._update_button_states)
        self.sequence_list.sequence_selected.connect(
            self._on_sequence_selected
        )


    def _on_sequence_selected(self, test_case):
        self.sequence_table.fn_load_sequence(test_case)

    def _create_vendor_combo(self):
        combo = PrimaryComboBox()
        combo.addItem("Vector", "vector")
        combo.setMaxVisibleItems(1)
        return combo

    def _create_device_combo(self):
        combo = PrimaryComboBox()
        combo.setMaxVisibleItems(10)
        fn_apply_scrollbar_style(combo.view())
        return combo

    def _create_channel_combo(self):
        combo = PrimaryComboBox()
        combo.setMaxVisibleItems(10)
        fn_apply_scrollbar_style(combo.view())
        return combo

    def _create_baudrate_combo(self):
        combo = PrimaryComboBox()
        for bitrate, label in self.BITRATES:
            combo.addItem(label, bitrate)
        combo.setCurrentIndex(2)
        combo.setMaxVisibleItems(len(self.BITRATES))
        fn_apply_scrollbar_style(combo.view())
        return combo

    @staticmethod
    def _create_inline_control(label, control):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(label)
        layout.addWidget(control, 1)
        return layout

    def refresh_can_setup(self):
        if self._closing or self._refreshing or self._connection_task.running or self._service.snapshot.state not in (State.DISCONNECTED, State.ERROR):
            return
        device = self.cmb_device.currentData()
        channel = self.cmb_channel.currentData()
        self._previous_device = device.identity if isinstance(device, CANDeviceInfo) else None
        self._previous_channel = channel.identity if isinstance(channel, CANChannelInfo) else None
        self._refreshing = True
        self._set_status("Discovering", "Searching for Vector CAN devices.")
        self._discovery_task.start()

    def _discovery_completed(self, devices):
        if self._closing:
            return
        self._refreshing = False
        # External connections must never be replaced by a late discovery result.
        if self._service.fn_is_connected():
            self._set_status("Connected")
            return
        with QSignalBlocker(self.cmb_device):
            self.cmb_device.clear()
            selected = 0
            for index, device in enumerate(devices):
                parts = [device.name]
                if device.serial is not None:
                    parts.append(f"SN {device.serial}")
                if device.hw_index is not None:
                    parts.append(f"HW {device.hw_type}:{device.hw_index}" if device.hw_type is not None else f"HW index {device.hw_index}")
                if device.hw_type is None or device.hw_index is None:
                    global_index = device.channels[0].channel_index if device.channels else None
                    parts.append(f"Index {global_index}" if global_index is not None else f"Discovery {index + 1}")
                self.cmb_device.addItem(" - ".join(parts), device)
                if device.identity == self._previous_device:
                    selected = index
            self.cmb_device.setCurrentIndex(selected if devices else -1)
        self._populate_device_channels()
        if not devices:
            self._set_status("No devices", "No Vector CAN device detected.")

    def _populate_device_channels(self):
        device = self.cmb_device.currentData()
        with QSignalBlocker(self.cmb_channel):
            self.cmb_channel.clear()
            selected = 0
            if isinstance(device, CANDeviceInfo):
                for index, channel in enumerate(device.channels):
                    self.cmb_channel.addItem(channel.name, channel)
                    if device.identity == self._previous_device and channel.identity == self._previous_channel:
                        selected = index
                self.cmb_channel.setCurrentIndex(selected if device.channels else -1)
        self._update_button_states()
        if (not self._refreshing and not self._connection_task.running and isinstance(device, CANDeviceInfo)
                and self._service.snapshot.state in (State.DISCONNECTED, State.ERROR)):
            if not device.channels:
                self._set_status("No CAN channel", "The detected Vector device has no available CAN channel.")
            else:
                self._set_status("Disconnected", "" if self._has_selection() else "The selected channel has no unambiguous global channel index.")

    def _discovery_failed(self, error):
        if self._closing:
            return
        self._refreshing = False
        if self._service.fn_is_connected():
            self._set_status("Connected")
            return
        self.cmb_device.clear()
        self.cmb_channel.clear()
        snapshot = self._service.snapshot
        state = (State.RECOVERY_REQUIRED.value if snapshot.state == State.RECOVERY_REQUIRED
                 else "No CAN channel" if isinstance(error, CANNoChannelsError) else "Error")
        message = snapshot.error if snapshot.state == State.RECOVERY_REQUIRED else str(error)
        self._set_status(state, message)
        self._show_error(message)

    def connect_can(self):
        if (self._closing or self._refreshing or self._connection_task.running or not self._has_selection()
                or self._service.snapshot.state not in (State.DISCONNECTED, State.ERROR)
                or self._service.snapshot.rediscovery_required):
            return

        try:
            config = self._read_config()
            self._set_status("Connecting")
            self._connection_task.start(Operation.CONNECT, config)
            self._update_button_states()
        except Exception as error:
            self._set_status("Error", str(error))
            self._show_error(str(error))
            return

    def disconnect_can(self):
        if (self._closing or self._refreshing or self._connection_task.running
                or self._service.snapshot.state != State.CONNECTED):
            return
        self._set_status("Disconnecting")
        self._connection_task.start(Operation.DISCONNECT)
        self._update_button_states()

    def _connection_completed(self, operation, snapshot):
        if self._closing:
            return
        config = snapshot.config
        details = (f"Vector SN {config.serial}, HW {config.hw_type}:{config.hw_index}, CAN {config.channel + 1}, global index {config.channel_index}, "
                   f"{config.bitrate} bit/s") if config else ""
        self._set_status(snapshot.state.value, details)

    def _connection_failed(self, operation, error):
        if self._closing:
            return
        snapshot = self._service.snapshot
        self._set_status(snapshot.state.value, str(error))
        self._show_error(str(error))

    def _read_config(self):
        if not self._has_selection():
            raise CANValidationError("Select a detected Vector CAN channel before connecting.")
        device = self.cmb_device.currentData()
        channel = self.cmb_channel.currentData()
        return CANConfig(
            interface=self.cmb_vendor.currentData(),
            channel=channel.channel,
            bitrate=int(self.cmb_baudrate.currentData()),
            serial=device.serial,
            channel_index=channel.channel_index,
            hw_type=device.hw_type,
            hw_index=device.hw_index,
            hw_channel=channel.hw_channel,
        )

    def _has_selection(self):
        device = self.cmb_device.currentData()
        channel = self.cmb_channel.currentData()
        return (isinstance(device, CANDeviceInfo) and isinstance(channel, CANChannelInfo)
                and channel in device.channels and channel.can_connect
                and (device.serial is not None or (device.hw_type is not None and device.hw_index is not None)))

    def _set_status(self, state, message=""):
        self._status_state = state
        self._status_message = message
        self.lbl_status.setText(state)
        self.lbl_status.setToolTip(message)
        self._update_button_states()
        self._refresh_status_theme()

    def _update_button_states(self):
        snapshot = self._service.snapshot
        idle = snapshot.state in (State.DISCONNECTED, State.ERROR)
        busy = self._connection_task.running or self._refreshing or self._closing
        self.btn_refresh.setEnabled(idle and not busy)
        self.btn_connect.setEnabled(idle and not busy and self._has_selection() and not snapshot.rediscovery_required)
        self.btn_disconnect.setEnabled(snapshot.state == State.CONNECTED and not busy)
        for combo in (self.cmb_vendor, self.cmb_device, self.cmb_channel, self.cmb_baudrate):
            combo.setEnabled(idle and not busy)

    def closeEvent(self, event):
        if not self._closing:
            self._closing = True
            self._discovery_task.dispose()
            self._connection_task.dispose()
        super().closeEvent(event)

    def _show_error(self, message):
        QMessageBox.warning(
            self,
            "CAN Interface",
            message,
        )

    def fn_refresh_theme(self):
        self.lbl_vendor.fn_refresh_theme()
        self.lbl_device.fn_refresh_theme()
        self.lbl_channel.fn_refresh_theme()
        self.lbl_baudrate.fn_refresh_theme()
        self.cmb_vendor.fn_refresh_theme()
        self.cmb_device.fn_refresh_theme()
        self.cmb_channel.fn_refresh_theme()
        self.cmb_baudrate.fn_refresh_theme()
        self.btn_refresh.fn_refresh_theme()
        self.btn_connect.fn_refresh_theme()
        self.btn_disconnect.fn_refresh_theme()
        self.sequence_list.fn_refresh_theme()
        self.sequence_table.fn_refresh_theme()
        self._refresh_status_theme()

    def _refresh_status_theme(self):
        colors = ThemeManager.fn_colors()
        state_colors = {
            "Disconnected": colors.SECONDARY_TEXT,
            "Connecting": colors.WARNING,
            "Disconnecting": colors.WARNING,
            "Recovery required": colors.DANGER,
            "Connected": colors.SUCCESS,
            "Error": colors.DANGER,
            "Discovering": colors.WARNING,
            "No devices": colors.SECONDARY_TEXT,
            "No CAN channel": colors.WARNING,
        }
        self.lbl_status.setStyleSheet(
            f"""
            QLabel {{
                color: {state_colors.get(self._status_state, colors.TEXT)};
                font-weight: 600;
            }}
            """
        )
