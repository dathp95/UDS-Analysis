

from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    
)

from gui.themes.theme_manager import ThemeManager
from gui.widgets.controls.primary_table import PrimaryTable

class ResultTable(PrimaryTable):
    def __init__(self):
        super().__init__()

        self._setup_ui()

        self._fn_setup_column_width()

        self.fn_refresh_theme()

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

        header = self.horizontalHeader()

        header.setSectionResizeMode(
            QHeaderView.Interactive
        )

        header.setStretchLastSection(False)

    def clear_data(self):
        self.setRowCount(0)
    


    def set_data(self, data):

        self.clear_data()     

        self.setRowCount(len(data))

        for row, item in enumerate(data):

            self.setItem(row, 0, self.fn_create_item(item["ECU"], row))
            self.setItem(row, 1, self.fn_create_item(item["Time"], row))
            self.setItem(row, 2, self.fn_create_item(item["Activity"], row))
            self.setItem(row, 3, self.fn_create_item(item["Request"], row))
            self.setItem(row, 4, self.fn_create_item(item["Response"], row))
            self.setItem(row, 5, self.fn_create_item(item["RT (ms)"], row))
            self.setItem(row, 6, self.fn_create_item(item["Status"], row))

   
    
    def _fn_setup_column_width(self):
        """
        Set default column widths.
        """

        self.setColumnWidth(
            self._fn_column_index("ECU"),
            120
        )

        self.setColumnWidth(
            self._fn_column_index("Time"),
            120
        )

       
        self.setColumnWidth(
            self._fn_column_index("Activity"),
            170
        )

        self.setColumnWidth(
            self._fn_column_index("Request"),
            180
        )

        self.setColumnWidth(
            self._fn_column_index("Response"),
            180
        )

        self.setColumnWidth(
            self._fn_column_index("RT (ms)"),
            80
        )

        self.setColumnWidth(
            self._fn_column_index("Status"),
            50
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
