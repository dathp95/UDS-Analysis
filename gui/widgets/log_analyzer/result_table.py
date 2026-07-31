

from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    
)
from PySide6.QtGui import QColor

from gui.themes.theme_manager import ThemeManager
from gui.widgets.controls.primary_table import PrimaryTable
from gui.utils.payload_format import format_payload_input

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
            80
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

        # Global search replaces Quick Filter highlighting.
        self._refresh_row_colors()

        keyword = format_payload_input(keyword.strip())
        keyword = " ".join(keyword.split()).lower()

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

        request = format_payload_input(
            filters.get("request", "").strip()
        )
        response = format_payload_input(
            filters.get("response", "").strip()
        )

        ecu_col = self._fn_column_index("ECU")

        request_col = self._fn_column_index("Request")
        response_col = self._fn_column_index("Response")

        colors = ThemeManager.fn_colors()

        self._refresh_row_colors()

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

                matched &= cell == request

            if response:
                item = self.item(row, response_col)
                cell = "" if item is None else " ".join(
                    item.text().strip().split()
                ).upper()
                if not request:
                    matched &= cell == response

                if request:
                    if cell == response:
                        background = colors.SUCCESS
                    elif not cell:
                        background = colors.DANGER
                    else:
                        background = colors.WARNING
                else:
                    background = None

                for column in range(self.columnCount()):
                    cell_item = self.item(row, column)
                    if cell_item is not None:
                        if background is None:
                            cell_item.setBackground(QColor(
                                colors.TABLE_ROW if row % 2 == 0 else colors.TABLE_ROW_ALT
                            ))
                        else:
                            cell_item.setBackground(QColor(background))

            self.setRowHidden(

                row,

                not matched

            )
    
    def fn_refresh_theme(self):

        super().fn_refresh_theme()
