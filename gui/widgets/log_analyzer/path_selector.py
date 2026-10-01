from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_lineedit import PrimaryLineEdit
from gui.widgets.log_analyzer.layout_constants import FORM_ACTION_BUTTON_WIDTH


class PathSelectorWidget(QWidget):

    path_changed = Signal(str)

    def __init__(self, title, file_filter):
        super().__init__()

        self.file_filter = file_filter
        self.label = QLabel(title)
        self.edit_path = PrimaryLineEdit(
            placeholder="Please, input file format *.blf/asc"
        )
        self.browse_button = PrimaryButton("Browse")
        self.browse_button.setFixedWidth(FORM_ACTION_BUTTON_WIDTH)

        self.set_ui()
        self.connect_signals()

    def set_ui(self):
        main_layout = QVBoxLayout(self)
        file_layout = QHBoxLayout()

        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)

        file_layout.setContentsMargins(0, 0, 0, 0)
        file_layout.setSpacing(8)

        file_layout.addWidget(
            self.edit_path,
            1,
        )
        file_layout.addWidget(self.browse_button)

        main_layout.addWidget(self.label)
        main_layout.addLayout(file_layout)


    def connect_signals(self):
        self.browse_button.clicked.connect(self.browse_file)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.label.text(),
            "",
            self.file_filter,
        )

        if file_path:
            self.edit_path.setText(file_path)
            self.path_changed.emit(file_path)

    def path(self):
        return self.edit_path.text()

    def set_path(self, value):
        self.edit_path.setText(value)

    def fn_refresh_theme(self):
        self.edit_path.fn_refresh_theme()
        self.browse_button.fn_refresh_theme()
