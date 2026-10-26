from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget, QComboBox
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_combobox import PrimaryComboBox
from gui.widgets.controls.primary_label import PrimaryLabel
from gui.themes.styles.controls.scrollbar_style import fn_apply_scrollbar_style


class CanConnectionPanel(QWidget):
    CONTROLS = ("lbl_vendor", "lbl_device", "lbl_channel", "lbl_baudrate", "cmb_vendor",
                "cmb_device", "cmb_channel", "cmb_baudrate", "btn_refresh", "btn_connect",
                "btn_disconnect", "lbl_status", "action_layout", "cmb_bench_policy")

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.title = PrimaryLabel("Connection")
        self.cmb_bench_policy = PrimaryComboBox(minimum_height=24)
        self.cmb_bench_policy.addItem('Standard: confirm state changes', None)
        self.cmb_bench_policy.addItem('I authorize test-bench diagnostics', 'manual-automotive-bench')
        self.cmb_bench_policy.setMinimumContentsLength(20)
        self.cmb_bench_policy.setMaximumWidth(275)
        self.cmb_bench_policy.setAccessibleName('Connection diagnostic authorization policy')
        self.cmb_bench_policy.setToolTip(
            'Before Connect, explicitly authorize this automotive test-bench connection.\n'
            'Only manual 10 01 (Default Session), 10 03 (Extended Session), and\n'
            '14 FF FF FF (clear all DTCs) skip per-request confirmation.\n'
            'Standard mode grants no bench authority. Disconnect expires this selection.')
        header = QHBoxLayout()
        header.addWidget(self.title, 1)
        header.addWidget(self.cmb_bench_policy)
        layout.addLayout(header)
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)
        for index, (key, label) in enumerate((("vendor", "Vendor"), ("device", "Device"),
                                              ("channel", "Channel"), ("baudrate", "Baudrate"))):
            text = PrimaryLabel(label)
            combo = PrimaryComboBox(minimum_height=30)
            combo.setMinimumContentsLength(6)
            combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            combo.setMaxVisibleItems(10)
            setattr(self, f"lbl_{key}", text)
            setattr(self, f"cmb_{key}", combo)
            row, col = divmod(index, 2)
            grid.addWidget(text, row, col * 2)
            grid.addWidget(combo, row, col * 2 + 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 2)
        self.cmb_vendor.addItem("Vector", "vector")
        for bitrate in (125000, 250000, 500000, 1000000):
            self.cmb_baudrate.addItem(f"{bitrate // 1000} kbit/s", bitrate)
        self.cmb_baudrate.setCurrentIndex(2)
        layout.addLayout(grid)
        self.action_layout = QHBoxLayout()
        self.action_layout.setSpacing(6)
        self.btn_refresh = PrimaryButton("Refresh", width=72, height=30)
        self.btn_connect = PrimaryButton("Connect", width=72, height=30)
        self.btn_disconnect = PrimaryButton("Disconnect", width=88, height=30)
        self.lbl_status = QLabel()
        self.lbl_status.setMinimumHeight(30)
        self.lbl_status.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        for widget in (self.btn_refresh, self.btn_connect, self.btn_disconnect, self.lbl_status):
            self.action_layout.addWidget(widget)
        self.action_layout.addStretch(1)
        layout.addLayout(self.action_layout)
        self.fn_refresh_theme()

    def fn_refresh_theme(self):
        self.title.fn_refresh_theme()
        for name in self.CONTROLS:
            widget = getattr(self, name)
            if hasattr(widget, "fn_refresh_theme"):
                widget.fn_refresh_theme()
            if isinstance(widget, PrimaryComboBox):
                fn_apply_scrollbar_style(widget.view())
