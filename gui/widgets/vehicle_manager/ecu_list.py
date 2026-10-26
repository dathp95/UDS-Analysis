from PySide6.QtCore import Qt, Signal, QSignalBlocker

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QSizePolicy,
    QMenu,
)

from gui.widgets.controls.primary_table import PrimaryTable
from gui.themes.styles.controls.scrollbar_style import (
    fn_apply_scrollbar_style,
)


class ECUList(PrimaryTable):

    ecu_selected = Signal(str)
    draft_discard_requested = Signal(str, str)

    def __init__(self):

        super().__init__()

        self._setup_table()
        self._dirty_names = set()
        self._draft_vehicle = ''
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._draft_menu)

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

            items[0].data(Qt.UserRole) or items[0].text()

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
            item.setData(Qt.UserRole, name)

            self.setItem(

                row,
                0,
                item,

            )

        self.setSortingEnabled(True)

        if ecu_names:

            self.selectRow(0)

    def fn_current_ecu_name(self) -> str:

        items = self.selectedItems()

        if not items:

            return ""

        return items[0].data(Qt.UserRole) or items[0].text()

    def fn_select_ecu(
        self,
        ecu_name: str,
    ) -> None:

        for row in range(self.rowCount()):

            item = self.item(
                row,
                0,
            )

            if item is None:

                continue

            if (item.data(Qt.UserRole) or item.text()) == ecu_name:

                self.selectRow(row)

                return

    def fn_set_dirty_names(self, names, vehicle_name=''):
        self._dirty_names = set(names)
        self._draft_vehicle = vehicle_name
        with QSignalBlocker(self):
            self.setSortingEnabled(False)
            for row in range(self.rowCount()):
                item = self.item(row, 0)
                if item is not None:
                    name = item.data(Qt.UserRole) or item.text()
                    item.setText(name + (' *' if name in names else ''))
            self.setSortingEnabled(True)

    def _draft_menu(self, position):
        item = self.itemAt(position)
        if item is None:
            return
        name = item.data(Qt.UserRole) or item.text()
        vehicle_name = self._draft_vehicle
        menu = QMenu(self)
        action = menu.addAction('Discard ECU draft')
        action.setEnabled(name in self._dirty_names)
        action.triggered.connect(lambda: self.draft_discard_requested.emit(vehicle_name, name))
        from gui.themes.styles.controls.menu_style import fn_apply_menu_style
        fn_apply_menu_style(menu)
        menu.exec(self.viewport().mapToGlobal(position))

    def fn_refresh_theme(self):

        super().fn_refresh_theme()

        fn_apply_scrollbar_style(self)
