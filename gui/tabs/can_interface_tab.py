from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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
from services.can import CANConfig, CANService


class CANInterfaceTab(QWidget):

    BITRATES = (
        (125000, "125 kbit/s"),
        (250000, "250 kbit/s"),
        (500000, "500 kbit/s"),
        (1000000, "1000 kbit/s"),
    )

    CHANNELS = (
        (0, "CAN 1"),
        (1, "CAN 2"),
        (2, "CAN 3"),
        (3, "CAN 4"),
    )

    DEVICES = (
        "VN1630A",
        "VN1640A",
    )

    def __init__(self, service=None):
        super().__init__()

        self._service = service or CANService()
        self._status_state = "Disconnected"
        self._status_message = ""

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
        combo.addItems(self.DEVICES)
        combo.setMaxVisibleItems(len(self.DEVICES))
        fn_apply_scrollbar_style(combo.view())
        return combo

    def _create_channel_combo(self):
        combo = PrimaryComboBox()
        for channel_index, label in self.CHANNELS:
            combo.addItem(label, channel_index)
        combo.setMaxVisibleItems(len(self.CHANNELS))
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
        try:
            self._service.fn_refresh()
        except Exception as error:
            self._set_status("Error", str(error))
            self._show_error(str(error))
            return

        if self._service.fn_is_connected():
            self._set_status("Connected")
        else:
            self._set_status("Disconnected")

    def connect_can(self):
        config = self._read_config()
        self._set_status("Connecting")

        try:
            self._service.fn_connect(config)
        except Exception as error:
            self._set_status("Error", str(error))
            self._show_error(str(error))
            return

        self._set_status("Connected")

    def disconnect_can(self):
        try:
            self._service.fn_disconnect()
        except Exception as error:
            self._set_status("Error", str(error))
            self._show_error(str(error))
            return

        self._set_status("Disconnected")

    def _read_config(self):
        return CANConfig(
            interface=self.cmb_vendor.currentData(),
            channel=int(self.cmb_channel.currentData()),
            bitrate=int(self.cmb_baudrate.currentData()),
        )

    def _set_status(self, state, message=""):
        self._status_state = state
        self._status_message = message
        self.lbl_status.setText(state)
        self.lbl_status.setToolTip(message)
        self._update_button_states()
        self._refresh_status_theme()

    def _update_button_states(self):
        is_connecting = self._status_state == "Connecting"
        is_connected = self._status_state == "Connected"
        try:
            is_connected = is_connected or self._service.fn_is_connected()
        except Exception:
            pass

        self.btn_refresh.setEnabled(not is_connecting)
        self.btn_connect.setEnabled(not is_connected and not is_connecting)
        self.btn_disconnect.setEnabled(is_connected and not is_connecting)

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
            "Connected": colors.SUCCESS,
            "Error": colors.DANGER,
        }
        self.lbl_status.setStyleSheet(
            f"""
            QLabel {{
                color: {state_colors.get(self._status_state, colors.TEXT)};
                font-weight: 600;
            }}
            """
        )
