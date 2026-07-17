from PySide6.QtCore import Qt

from PySide6.QtGui import QColor

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)
from gui.themes.theme_manager import ThemeManager

from gui.themes.styles.controls.table_style import (
    fn_table_style
)


class PrimaryTable(QTableWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self._setup_primary_table()

    # ==========================================
    # Private
    # ==========================================

    def _setup_primary_table(self):

        self.setAlternatingRowColors(False)

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

        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)

        self.fn_refresh_theme()

    # ==========================================
    # Public
    # ==========================================
    def fn_create_item(
            self,
            value,
            row,
            alignment=Qt.AlignLeft | Qt.AlignVCenter,
            foreground=None,
            background=None,
        ):
        """
        Create a styled table item.

        Parameters
        ----------
        value
            Cell text.

        row
            Current row index.

        alignment
            Qt alignment.

        foreground
            Optional text color.

        background
            Optional background color.

        Returns
        -------
        QTableWidgetItem
        """

        colors = ThemeManager.fn_colors()

        item = QTableWidgetItem(str(value))

        item.setTextAlignment(alignment)

        # Default alternating background
        if background is None:

            background = (
                colors.TABLE_ROW
                if row % 2 == 0
                else colors.TABLE_ROW_ALT
            )

        item.setBackground(QColor(background))

        if foreground is not None:

            item.setForeground(QColor(foreground))

        return item
    
    def _refresh_row_colors(self):

        colors = ThemeManager.fn_colors()

        for row in range(self.rowCount()):

            bg = (
                colors.TABLE_ROW
                if row % 2 == 0
                else colors.TABLE_ROW_ALT
            )

            for col in range(self.columnCount()):

                item = self.item(row,col)

                if item:

                    item.setBackground(QColor(bg))

    def fn_refresh_theme(self):

        self.setStyleSheet(
            fn_table_style()
        )

        self._refresh_row_colors()
    