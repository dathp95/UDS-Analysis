from PySide6.QtCore import Signal

from gui.widgets.controls.primary_table import PrimaryTable


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