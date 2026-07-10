from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QWidget,
    QGroupBox,    
    QVBoxLayout,
    QPushButton
)

from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.theme_switch import ThemeSwitch


class ActionPanel (QWidget):
    analyze_clicked = Signal()
    export_clicked = Signal()
    copy_clicked = Signal()
    clear_clicked = Signal()

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        group_box = QGroupBox("Actions")
        group_layout = QVBoxLayout(group_box)

        # self.theme_switch = ThemeSwitch()


        self.btn_run = PrimaryButton("RUN", width=200, height=50)                                      
        self.btn_export = PrimaryButton("EXPORT", width = 160)                                      
        self.btn_copy = PrimaryButton("COPY")                                      
        
        self.btn_clear = PrimaryButton("CLEAR")

        group_layout.addWidget(self.btn_run)
        group_layout.addWidget(self.btn_export)
        group_layout.addWidget(self.btn_copy)
        group_layout.addWidget(self.btn_clear)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(group_box)

        # main_layout.addWidget(self.theme_switch)

        main_layout.addStretch()

    def _connect_signals (self):
        self.btn_run.clicked.connect(
            self.analyze_clicked.emit
        )
        self.btn_export.clicked.connect(
            self.export_clicked.emit
        )
        self.btn_copy.clicked.connect(
            self.copy_clicked.emit
        )
        self.btn_clear.clicked.connect(
            self.clear_clicked.emit
        )
    
    
    def _fn_enable_buttons(
            self,
            run: bool,
            export: bool,
            copy: bool,
            clear: bool
        ):

        self.btn_run.setEnabled(run)

        self.btn_export.setEnabled(export)

        self.btn_copy.setEnabled(copy)

        self.btn_clear.setEnabled(clear)

    def fn_set_startup_state(self):

        self._fn_enable_buttons(

            run=False,
            export=False,
            copy=False,
            clear=False

        )   

    def fn_set_file_loaded_state(self):

        self._fn_enable_buttons(

            run=True,
            export=False,
            copy=False,
            clear=False

        ) 
    
    def fn_set_analyzed_state(self):

        self._fn_enable_buttons (
            run = True,
            export = True,
            copy = True,
            clear = True
        )
    
    def fn_set_empty_state (self):
        self._fn_enable_buttons(
            run = True,
            export = False,
            copy = False,
            clear= False 
        )
    
    def fn_refresh_theme(self):

        self.btn_run.fn_refresh_theme()

        self.btn_export.fn_refresh_theme()

        self.btn_copy.fn_refresh_theme()

        self.btn_clear.fn_refresh_theme()
                                              
