
from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    
)
from gui.widgets.controls.primary_table import (
    PrimaryTable
)


class ResultTable(PrimaryTable):
    def __init__(self):
        super().__init__()

        self._setup_ui()
        # self._setup_columns()

    def _setup_ui(self):
        headers = [
            "ECU",
            "Time",
            "Activity",
            "Request",
            "Response",
            "RT (ms)",
            "Status"
        ]

        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

    

    def clear_data(self):
        self.setRowCount(0)

    def set_data(self, data):

        self.clear_data()

        self.setRowCount(len(data))

        for row, item in enumerate(data):

            self.setItem(
                row,
                0,
                QTableWidgetItem(item["ECU"])
            )

            self.setItem(
                row,
                1,
                QTableWidgetItem(str(item["Time"]))
            )

            
            self.setItem(
                row,
                2,
                QTableWidgetItem(item["Activity"])
            )

            self.setItem(
                row,
                3,
                QTableWidgetItem(item["Request"])
            )

            self.setItem(
                row,
                4,
                QTableWidgetItem(item["Response"])
            )

            self.setItem(
                row,
                5,
                QTableWidgetItem(str(item["RT (ms)"]))
            )

            self.setItem(
                row,
                6,
                QTableWidgetItem(item["Status"])
            )
    
    def fn_search(
            self,
            keyword: str = "",
        ):
        """
        Filter table rows by keyword.

        Search is:
        - Case-insensitive.
        - Ignores leading/trailing spaces.
        - Normalizes multiple spaces into one.
        """

        # ------------------------------------------
        # Normalize user input
        # ------------------------------------------

        keyword = " ".join(
            keyword.strip().split()
        ).lower()

        # Empty keyword -> show all rows
        if not keyword:

            for row in range(self.rowCount()):

                self.setRowHidden(
                    row,
                    False
                )

            return

        # ------------------------------------------
        # Search every cell
        # ------------------------------------------

        for row in range(self.rowCount()):

            matched = False

            for column in range(self.columnCount()):

                item = self.item(row, column)

                if item is None:
                    continue

                cell_text = " ".join(
                    item.text().strip().split()
                ).lower()

                if keyword in cell_text:

                    matched = True
                    break

            self.setRowHidden(
                row,
                not matched
            )

  
    def _fn_column_index(
            self,
            header: str,
        ) -> int:
        """
        Return the column index by header text.

        Raises
        ------
        ValueError
            If the header does not exist.
        """

        for column in range(self.columnCount()):

            item = self.horizontalHeaderItem(column)

            if item is None:

                continue

            if item.text().strip().lower() == header.lower():

                return column

        raise ValueError(

            f"Column '{header}' not found."

        )
    
    def fn_apply_quick_filter(
            self,
            filter_data: dict,
        ):
        """
        Apply one quick filter.

        Empty filter fields are ignored.
        All non-empty fields must match (AND logic).
        """

        filters = filter_data.get(
            "filters",
            {}
        )

        ecu = filters.get("ecu", "").strip().upper()

        request = filters.get("request","").strip().upper()

        ecu_col = self._fn_column_index("ECU")

        request_col = self._fn_column_index("Request")

        for row in range(self.rowCount()):

            matched = True

            # --------------------------
            # ECU
            # --------------------------

            if ecu:

                item = self.item(
                    row,
                    ecu_col
                )

                cell = ""

                if item is not None:

                    cell = item.text().strip().upper()

                matched &= ecu in cell

            # --------------------------
            # Request
            # --------------------------

            if request:

                item = self.item(
                    row,
                    request_col
                )

                cell = ""

                if item is not None:

                    cell = " ".join(
                        item.text().strip().split()
                    ).upper()

                matched &= request in cell

            self.setRowHidden(

                row,

                not matched

            )
    
    def fn_refresh_theme(self):

        super().fn_refresh_theme()
