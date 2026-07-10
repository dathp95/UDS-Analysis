# TODO: FORMAT TABLE
"""
    Provide a reusable table control.

    It knows:

    Theme
    Default behavior
    Default appearance

    It does NOT know:

    Transactions
    ECU
    UDS
    Business Logic

"""

from PySide6.QtWidgets import (
    QTableWidget,
    QHeaderView,
    QAbstractItemView
)

from gui.themes.styles.controls.table_style import (
    fn_table_style
)


class PrimaryTable(QTableWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self._setup_ui()

    # ==========================================
    # Private
    # ==========================================

    def _setup_ui(self):

        self.setAlternatingRowColors(True)

        self.setSortingEnabled(True)

        self.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.verticalHeader().setVisible(False)

        self.horizontalHeader().setStretchLastSection(True)

        self.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        self.fn_refresh_theme()

    # ==========================================
    # Public
    # ==========================================

    def fn_refresh_theme(self):

        self.setStyleSheet(
            fn_table_style()
        )