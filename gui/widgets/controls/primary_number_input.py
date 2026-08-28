from PySide6.QtCore import Signal
from PySide6.QtWidgets import QAbstractSpinBox, QHBoxLayout, QWidget

from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_spinbox import PrimarySpinBox


class PrimaryNumberInput(QWidget):

    valueChanged = Signal(int)

    def __init__(
        self,
        value_width: int = 70,
        button_width: int = 32,
        height: int = 36,
        parent=None,
    ):
        super().__init__(parent)

        self._value_width = value_width
        self._button_width = button_width
        self._height = height

        self._setup_ui()
        self._connect_signals()
        self.fn_refresh_theme()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.btn_decrement = PrimaryButton(
            "-",
            width=self._button_width,
            height=self._height,
        )
        self.spinbox = PrimarySpinBox(minimum_height=self._height)
        self.btn_increment = PrimaryButton(
            "+",
            width=self._button_width,
            height=self._height,
        )

        self.btn_decrement.setFixedWidth(self._button_width)
        self.btn_increment.setFixedWidth(self._button_width)
        self.btn_decrement.setFixedHeight(self._height)
        self.btn_increment.setFixedHeight(self._height)
        self.spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spinbox.setFixedWidth(self._value_width)
        self.spinbox.setMinimumHeight(self._height)

        layout.addWidget(self.btn_decrement)
        layout.addWidget(self.spinbox)
        layout.addWidget(self.btn_increment)

    def _connect_signals(self):
        self.btn_decrement.clicked.connect(self.stepDown)
        self.btn_increment.clicked.connect(self.stepUp)
        self.spinbox.valueChanged.connect(self.valueChanged.emit)

    def value(self):
        return self.spinbox.value()

    def setValue(self, value):
        self.spinbox.setValue(value)

    def minimum(self):
        return self.spinbox.minimum()

    def setMinimum(self, value):
        self.spinbox.setMinimum(value)

    def maximum(self):
        return self.spinbox.maximum()

    def setMaximum(self, value):
        self.spinbox.setMaximum(value)

    def setRange(self, minimum, maximum):
        self.spinbox.setRange(minimum, maximum)

    def singleStep(self):
        return self.spinbox.singleStep()

    def setSingleStep(self, step):
        self.spinbox.setSingleStep(step)

    def stepUp(self):
        self.spinbox.stepUp()

    def stepDown(self):
        self.spinbox.stepDown()

    def blockSignals(self, block):
        self.spinbox.blockSignals(block)
        return super().blockSignals(block)

    def fn_refresh_theme(self):
        self.btn_decrement.fn_refresh_theme()
        self.spinbox.fn_refresh_theme()
        self.spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.btn_increment.fn_refresh_theme()