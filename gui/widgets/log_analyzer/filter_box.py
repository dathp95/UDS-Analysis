
from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QLabel,
    QVBoxLayout,
    QHBoxLayout
)

from PySide6.QtCore import Signal

from gui.widgets.controls.primary_lineedit import PrimaryLineEdit



class FilterBox(QWidget):
    
    filter_changed = Signal(str)

    def __init__(
            self,
            title = "",
        ):
        super().__init__()
        self.label_title = QLabel(title)
        self.edit_filter= PrimaryLineEdit(
                placeholder="Search ECU, NAME DIDS, Request, Response..."
                )

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        filter_box_layout = QHBoxLayout()

        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)

        filter_box_layout.setContentsMargins(0, 0, 0, 0)
        filter_box_layout.setSpacing(8)

        # filter_box_layout.addWidget(self.label_title)
        filter_box_layout.addWidget(self.edit_filter)

        main_layout.addLayout(filter_box_layout)

    def _connect_signals(self):
        self.edit_filter.textChanged.connect(
            self.filter_changed.emit
        )
        

    # ==========================
    # Public API
    # ==========================        

    def text(self):
        return self.edit_filter.text()
    
    def clear(self):
        self.edit_filter.clear()
    
    def set_text(self, text: str):

        self.edit_filter.setText(text)


    def set_placeholder(self, text: str):

        self.edit_filter.setPlaceholderText(text)


    def set_focus(self):

        self.edit_filter.setFocus()
    
    def fn_refresh_theme(self):

        self.edit_filter.fn_refresh_theme()
            
        
    
