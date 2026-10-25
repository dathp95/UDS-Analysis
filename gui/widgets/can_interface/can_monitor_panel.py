from collections import deque
from PySide6.QtCore import QThread, Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from core.can_interface_view import CanFrameView
from gui.widgets.controls.action_button import ActionButton
from gui.widgets.controls.primary_combobox import PrimaryComboBox
from gui.widgets.controls.primary_lineedit import PrimaryLineEdit
from gui.widgets.controls.primary_label import PrimaryLabel
from gui.widgets.controls.primary_table import PrimaryTable
from gui.widgets.can_interface.panel_theme import apply_panel_theme


class CanMonitorPanel(QWidget):
    def __init__(self, capacity=2000):
        super().__init__()
        if isinstance(capacity, bool) or not isinstance(capacity, int) or not 1 <= capacity <= 10000:
            raise ValueError("Monitor display capacity must be in range 1..10000.")
        self._buffer = deque(maxlen=capacity)
        self.frames = self.displayed = self.dropped = 0
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        header = QHBoxLayout()
        self.title = PrimaryLabel("CAN Monitor")
        self.status = PrimaryLabel("Not monitoring")
        self.btn_clear = ActionButton("Clear", width=55, height=30)
        self.btn_export = ActionButton("Export CSV", width=85, height=30)
        self.btn_blf = ActionButton("Start BLF Log", width=100, height=30)
        self.btn_export.setEnabled(False)
        self.btn_blf.setEnabled(False)
        self.btn_export.setToolTip("CSV export is not implemented in this UI milestone.")
        self.btn_blf.setToolTip("Raw CAN BLF logging is not implemented in this UI milestone.")
        header.addWidget(self.title, 1)
        header.addWidget(self.status)
        for button in (self.btn_clear, self.btn_export, self.btn_blf): header.addWidget(button)
        filters = QHBoxLayout()
        self.edit_can_id = PrimaryLineEdit("CAN ID filter (HEX)")
        self.cmb_direction = PrimaryComboBox(minimum_height=30)
        self.cmb_direction.addItems(("All", "TX", "RX"))
        filters.addWidget(self.edit_can_id, 1)
        filters.addWidget(self.cmb_direction)
        self.table = PrimaryTable()
        self.table.setSortingEnabled(False)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(("Time (s)", "Dir", "CAN ID", "DLC", "Data (HEX)"))
        self.table.verticalHeader().setDefaultSectionSize(30)
        for column, width in enumerate((85, 45, 85, 45, 180)): self.table.setColumnWidth(column, width)
        self.feedback = PrimaryLabel("")
        self.feedback.hide()
        self.counters = PrimaryLabel("")
        layout.addLayout(header)
        layout.addLayout(filters)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.feedback)
        layout.addWidget(self.counters)
        self.btn_clear.clicked.connect(self.clear_display)
        self.edit_can_id.textChanged.connect(self._render)
        self.cmb_direction.currentTextChanged.connect(self._render)
        self._render()

    def append_frame_batch(self, frames):
        if QThread.currentThread() != self.thread():
            raise RuntimeError("Monitor view updates must run on the GUI thread.")
        try:
            for frame in frames:
                if not isinstance(frame, CanFrameView):
                    raise TypeError("Expected CanFrameView presentation data.")
                if len(self._buffer) == self._buffer.maxlen:
                    self.dropped += 1
                self._buffer.append(frame)
                self.frames += 1
        finally:
            self._render()

    def clear_display(self):
        self._buffer.clear()
        self.frames = self.displayed = self.dropped = 0
        self._render()

    def set_monitoring_state(self, state):
        if state != "Not monitoring":
            raise NotImplementedError("Live monitoring is unavailable in M03.")
        self.status.setText(state)

    def set_logging_state(self, state, path=None):
        if state != "Stopped" or path is not None:
            raise NotImplementedError("BLF logging is unavailable in M03.")

    def _render(self, *_):
        text = self.edit_can_id.text().strip()
        try:
            can_id = int(text, 16) if text else None
            if can_id is not None and not 0 <= can_id <= 0x1FFFFFFF:
                raise ValueError()
            self.feedback.clear()
            self.feedback.hide()
            frames = [frame for frame in self._buffer if (can_id is None or frame.can_id == can_id)
                      and (self.cmb_direction.currentText() == 'All' or frame.direction == self.cmb_direction.currentText())]
        except ValueError:
            frames = []
            self.feedback.setText("Invalid CAN ID filter. Enter HEX digits.")
            self.feedback.show()
        self.table.setRowCount(len(frames))
        for row, frame in enumerate(frames):
            values = (f"{frame.timestamp_s:.6f}", frame.direction, f"{frame.can_id:03X}" if frame.can_id <= 0x7FF else f"{frame.can_id:08X}", str(frame.dlc), frame.data.hex(' ').upper())
            for column, value in enumerate(values):
                item = self.table.fn_create_item(value, row)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setToolTip(value)
                if column == 4: item.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
                self.table.setItem(row, column, item)
        self.displayed = len(frames)
        self.counters.setText(f"Frames: {self.frames}    Displayed: {self.displayed}    Dropped: {self.dropped}")

    def fn_refresh_theme(self):
        apply_panel_theme(self, "canMonitorPanel")
        self.title.fn_refresh_theme()
        self.table.fn_refresh_theme()
        for widget in (self.status, self.btn_clear, self.btn_export, self.btn_blf, self.edit_can_id, self.cmb_direction, self.feedback, self.counters):
            widget.fn_refresh_theme()
        from gui.themes.styles.controls.scrollbar_style import fn_apply_scrollbar_style
        fn_apply_scrollbar_style(self.cmb_direction.view())
