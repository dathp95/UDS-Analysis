from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QWidget,
    QGroupBox,    
    QVBoxLayout,
    QHBoxLayout,
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
        # container = QWidget()
        layout = QVBoxLayout(self)

        # self.theme_switch = ThemeSwitch()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)


        self.btn_run = PrimaryButton("Analyze", width=160, height=50)                                      
        self.btn_export = PrimaryButton("EXPORT", width = 160)                                      
        self.btn_copy = PrimaryButton("COPY ASC DATA", width = 160)
        self.btn_clear = PrimaryButton("CLEAR TABLE", height = 50)

        layout.addStretch()
        layout.addWidget(self.btn_run)
        layout.addSpacing(12)
        layout.addWidget(self.btn_export)
        layout.addWidget(self.btn_copy)
        layout.addWidget(self.btn_clear)
        layout.addStretch()

        # main_layout = QVBoxLayout(self)
        # main_layout.setContentsMargins(0, 0, 0, 0)
        # main_layout.addWidget(container)

        # main_layout.addWidget(self.theme_switch)


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

    # ==========================================================================
    # Function: fn_set_file_loaded_state
    #
    # Purpose:
    #     Set action buttons after a log file is selected.
    #
    # Inputs:
    #     self: ActionPanel instance.
    #
    # Outputs:
    #     None.
    #
    # Called by:
    #     MainWindow.fn_log_file_changed()
    #
    # Calls:
    #     ActionPanel._fn_enable_buttons()
    #
    # Side Effects:
    #     Updates enabled/disabled state of action buttons.
    #
    # Responsibility:
    #     Enable RUN while keeping COPY disabled until analysis is complete.
    #
    # Does NOT:
    #     - Run analysis.
    #     - Copy ASC content.
    #     - Export Excel.
    #     - Clear table data.
    #     - Change selected file path.
    #
    # ==========================================================================
    def fn_set_file_loaded_state(self) -> None:
        """Update action buttons after the user selects a log file."""

        self._fn_enable_buttons(

            run=True,
            export=False,
            copy=False,
            clear=False

        ) 
    
    # ==========================================================================
    # Function: fn_set_analyzed_state
    #
    # Purpose:
    #     Set action buttons after analysis has completed.
    #
    # Inputs:
    #     self: ActionPanel instance.
    #
    # Outputs:
    #     None.
    #
    # Called by:
    #     MainWindow.fn_run_clicked()
    #
    # Calls:
    #     ActionPanel._fn_enable_buttons()
    #
    # Side Effects:
    #     Enables result actions such as EXPORT, COPY, and CLEAR.
    #
    # Responsibility:
    #     Make COPY active only after RUN has produced analysis data.
    #
    # Does NOT:
    #     - Run analysis.
    #     - Copy ASC content.
    #     - Export Excel.
    #     - Modify result table data.
    #     - Change selected file path.
    #
    # ==========================================================================
    def fn_set_analyzed_state(self) -> None:
        """Update action buttons after analysis is complete."""

        self._fn_enable_buttons (
            run = True,
            export = True,
            copy = True,
            clear = True
        )
    
    # ==========================================================================
    # Function: fn_set_empty_state
    #
    # Purpose:
    #     Set action buttons after result data has been cleared.
    #
    # Inputs:
    #     self: ActionPanel instance.
    #
    # Outputs:
    #     None.
    #
    # Called by:
    #     MainWindow.fn_clear_clicked()
    #
    # Calls:
    #     ActionPanel._fn_enable_buttons()
    #
    # Side Effects:
    #     Updates enabled/disabled state of RUN, EXPORT, COPY, and CLEAR buttons.
    #
    # Responsibility:
    #     Keep the button state consistent after the table is cleared.
    #
    # Does NOT:
    #     - Clear table data.
    #     - Clear filter text.
    #     - Remove the selected file path.
    #     - Export Excel.
    #     - Run analysis.
    #
    # ==========================================================================
    def fn_set_empty_state(self) -> None:
        """Update action buttons for an empty result table state."""
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
                                              
