from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QSizePolicy, QVBoxLayout, QWidget
from gui.widgets.controls.primary_label import PrimaryLabel
from html import escape


class CurrentTestCasePanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.title = PrimaryLabel("Current Test Case")
        self.empty = PrimaryLabel("Select a diagnostic row.")
        layout.addWidget(self.title)
        layout.addWidget(self.empty)
        self.fields = QWidget()
        grid = QGridLayout(self.fields)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(4)
        self.labels, self.values = {}, {}
        positions = {"Step": (0, 0, 1), "ECU": (0, 2, 1), "Payload": (1, 0, 3),
                     "Expected": (2, 0, 3), "Delay": (3, 0, 1), "Repeat": (3, 2, 1)}
        for name, (row, column, span) in positions.items():
            label = PrimaryLabel(name)
            value = PrimaryLabel("—")
            value.setTextFormat(Qt.PlainText)
            value.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
            value.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            value.setMinimumWidth(40)
            grid.addWidget(label, row, column)
            grid.addWidget(value, row, column + 1, 1, span)
            self.labels[name], self.values[name] = label, value
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        layout.addWidget(self.fields)
        self.dll_status = PrimaryLabel("DLL: select a diagnostic row and Vehicle.")
        self.dll_status.setTextFormat(Qt.PlainText)
        self.dll_status.setWordWrap(True)
        self.dll_status.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.dll_status)
        layout.addStretch(1)
        self.display_step()

    def display_step(self, step=None, total=0):
        self.empty.setVisible(step is None)
        self.fields.setVisible(step is not None)
        if step is None:
            for value in self.values.values(): value.setText("—")
            return
        values = dict(Step=f"{step.step} / {total}", ECU=step.ecu, Payload=step.request,
                      Expected=step.expected_response or "—", Delay="—" if step.delay_ms is None else f"{step.delay_ms} ms", Repeat=str(step.repeat))
        for name, text in values.items():
            self.values[name].setText(text)
            self.values[name].setToolTip(escape(text))

    def fn_refresh_theme(self):
        self.title.fn_refresh_theme()
        self.empty.fn_refresh_theme()
        self.dll_status.fn_refresh_theme()
        for widget in (*self.labels.values(), *self.values.values()):
            widget.fn_refresh_theme()
