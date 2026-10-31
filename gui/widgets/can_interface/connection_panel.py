from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QWidget,
    QComboBox,
    QSizePolicy,
)
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_combobox import PrimaryComboBox
from gui.widgets.controls.primary_label import PrimaryLabel
from gui.themes.styles.controls.scrollbar_style import fn_apply_scrollbar_style


class CanConnectionPanel(QWidget):
    CONTROLS = (
        "lbl_vendor",
        "lbl_device",
        "lbl_channel",
        "lbl_baudrate",
        "cmb_vendor",
        "cmb_device",
        "cmb_channel",
        "cmb_baudrate",
        "btn_refresh",
        "btn_connect",
        "btn_disconnect",
        "lbl_status",
        "action_layout",
        "cmb_bench_policy",
    )

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setFixedHeight(34)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 2, 4, 2)
        main_layout.setSpacing(6)
        main_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # 1. Toggle button for collapsible details (<< / >>)
        self.btn_toggle_details = PrimaryButton("<<", width=30, height=26)
        self.btn_toggle_details.setToolTip("Show/hide connection details (Vendor, Device, Baudrate)")
        self.btn_toggle_details.clicked.connect(self._toggle_details)
        main_layout.addWidget(self.btn_toggle_details)

        # 2. Hidden-by-default details panel (Vendor, Device, Baudrate, Policy, Refresh)
        self.details_widget = QWidget()
        details_layout = QHBoxLayout(self.details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(6)

        self.lbl_vendor = PrimaryLabel("Vendor")
        self.cmb_vendor = PrimaryComboBox(minimum_height=26)
        self.cmb_vendor.setMinimumContentsLength(6)
        self.cmb_vendor.addItem("Vector", "vector")
        details_layout.addWidget(self.lbl_vendor)
        details_layout.addWidget(self.cmb_vendor)

        self.lbl_device = PrimaryLabel("Device")
        self.cmb_device = PrimaryComboBox(minimum_height=26)
        self.cmb_device.setMinimumContentsLength(8)
        self.cmb_device.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.cmb_device.setMaxVisibleItems(10)
        details_layout.addWidget(self.lbl_device)
        details_layout.addWidget(self.cmb_device)

        self.lbl_baudrate = PrimaryLabel("Baudrate")
        self.cmb_baudrate = PrimaryComboBox(minimum_height=26)
        for bitrate in (125000, 250000, 500000, 1000000):
            self.cmb_baudrate.addItem(f"{bitrate // 1000} kbit/s", bitrate)
        self.cmb_baudrate.setCurrentIndex(2)
        details_layout.addWidget(self.lbl_baudrate)
        details_layout.addWidget(self.cmb_baudrate)

        self.cmb_bench_policy = PrimaryComboBox(minimum_height=26)
        self.cmb_bench_policy.addItem("Standard", None)
        self.cmb_bench_policy.addItem("Authorize bench", "manual-automotive-bench")
        self.cmb_bench_policy.setToolTip("Connection diagnostic authorization policy")
        details_layout.addWidget(self.cmb_bench_policy)

        self.details_widget.hide()
        main_layout.addWidget(self.details_widget)

        # 3. Always visible Channel selector
        self.lbl_channel = PrimaryLabel("Channel")
        self.cmb_channel = PrimaryComboBox(minimum_height=26)
        self.cmb_channel.setMinimumContentsLength(6)
        self.cmb_channel.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.cmb_channel.setMaxVisibleItems(10)
        main_layout.addWidget(self.lbl_channel)
        main_layout.addWidget(self.cmb_channel)

        # 4. Action layout: strict order [btn_refresh, btn_connect, btn_disconnect, lbl_status] for test compatibility
        self.btn_refresh = PrimaryButton("Refresh", width=62, height=26)
        self.btn_connect = PrimaryButton("Connect", width=80, height=26)
        self.btn_disconnect = PrimaryButton("Disconnect", width=80, height=26)
        self.btn_disconnect.hide()
        self.btn_connect.hide()

        # Single visible unified Connect / Disconnect button
        self.btn_action = PrimaryButton("Connect", width=84, height=26)
        self.btn_action.clicked.connect(self._on_action_clicked)

        self.lbl_status = QLabel("Disconnected")
        self.lbl_status.setMinimumHeight(26)
        self.lbl_status.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.lbl_status.setStyleSheet("font-weight: bold; color: #94a3b8;")

        self.lbl_status_dot = QLabel("●")
        self.lbl_status_dot.setFixedSize(14, 26)
        self.lbl_status_dot.setAlignment(Qt.AlignCenter)
        self.lbl_status_dot.setStyleSheet("color: #94a3b8; font-size: 14px;")

        self.action_layout = QHBoxLayout()
        self.action_layout.setContentsMargins(0, 0, 0, 0)
        self.action_layout.setSpacing(6)
        self.action_layout.addWidget(self.btn_refresh)
        self.action_layout.addWidget(self.btn_connect)
        self.action_layout.addWidget(self.btn_disconnect)
        self.action_layout.addWidget(self.lbl_status)

        status_container = QWidget()
        status_box = QHBoxLayout(status_container)
        status_box.setContentsMargins(0, 0, 0, 0)
        status_box.setSpacing(4)
        status_box.addWidget(self.lbl_status_dot)
        status_box.addWidget(self.lbl_status)

        main_layout.addWidget(self.btn_action)
        main_layout.addWidget(status_container)

        self.title = PrimaryLabel("Connection")
        self.fn_refresh_theme()

    def _on_action_clicked(self):
        if self.btn_disconnect.isEnabled() and self.btn_action.text() == "Disconnect":
            self.btn_disconnect.click()
        elif self.btn_connect.isEnabled():
            self.btn_connect.click()

    def _toggle_details(self):
        is_hidden = self.details_widget.isHidden()
        self.details_widget.setVisible(is_hidden)
        self.btn_refresh.setVisible(is_hidden)
        self.btn_toggle_details.setText(">>" if is_hidden else "<<")

    def fn_refresh_theme(self):
        if hasattr(self, "title") and hasattr(self.title, "fn_refresh_theme"):
            self.title.fn_refresh_theme()
        for name in self.CONTROLS:
            widget = getattr(self, name)
            if hasattr(widget, "fn_refresh_theme"):
                widget.fn_refresh_theme()
            if isinstance(widget, PrimaryComboBox):
                fn_apply_scrollbar_style(widget.view())
