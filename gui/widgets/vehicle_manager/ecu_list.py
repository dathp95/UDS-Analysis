from PySide6.QtCore import Qt, Signal

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QSizePolicy,
)

from gui.widgets.controls.primary_table import PrimaryTable
from gui.themes.styles.controls.scrollbar_style import (
    fn_apply_scrollbar_style,
)


class ECUList(PrimaryTable):

    ecu_selected = Signal(str)

    def __init__(self):

        super().__init__()

        self._setup_table()

        self.itemSelectionChanged.connect(

            self._on_selection_changed

        )

    # ==========================================
    # Private
    # ==========================================

    def _setup_table(self):

        self.setColumnCount(1)

        self.setHorizontalHeaderLabels(

            ["ECU"]

        )

        self.setMinimumWidth(220)

        self.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Expanding,
        )

        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.setVerticalScrollMode(
            QAbstractItemView.ScrollPerPixel
        )

        self.setHorizontalScrollMode(
            QAbstractItemView.ScrollPerPixel
        )

        self.setShowGrid(False)

        self.setAlternatingRowColors(False)

        self.setWordWrap(False)

        self.verticalHeader().setDefaultSectionSize(34)

        header = self.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.Stretch,
        )

        fn_apply_scrollbar_style(self)

    def _on_selection_changed(self):

        items = self.selectedItems()

        if not items:

            return

        self.ecu_selected.emit(

            items[0].text()

        )

    # ==========================================
    # Public
    # ==========================================

    def fn_set_ecus(
        self,
        ecu_names: list[str],
    ):

        self.setSortingEnabled(False)

        self.setRowCount(

            len(ecu_names)

        )

        for row, name in enumerate(ecu_names):

            item = self.fn_create_item(

                name,
                row,

            )

            self.setItem(

                row,
                0,
                item,

            )

        self.setSortingEnabled(True)

        if ecu_names:

            self.selectRow(0)

    def fn_refresh_theme(self):

        super().fn_refresh_theme()

        fn_apply_scrollbar_style(self)
