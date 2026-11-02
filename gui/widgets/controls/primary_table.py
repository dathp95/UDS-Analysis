from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)
from gui.themes.theme_manager import ThemeManager

from gui.themes.styles.controls.table_style import (
    fn_table_style
)

from gui.themes.styles.controls.scrollbar_style import (
    fn_apply_scrollbar_style,
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

        fn_apply_scrollbar_style(self)

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


    
    def fn_enable_one_click_edit(self):
        """Enable immediate editing on editable table cells."""
        if getattr(self, "_one_click_edit_enabled", False):
            return

        self._one_click_edit_enabled = True

        # Keep keyboard editing, but do not require double-click.
        self.setEditTriggers(
            QAbstractItemView.EditKeyPressed
            | QAbstractItemView.AnyKeyPressed
        )

        self.cellClicked.connect(self._on_editable_cell_clicked)


    
    def _on_editable_cell_clicked(self, row, column):
        """Open editor immediately on a single click."""

        modifiers = QApplication.keyboardModifiers()

        if modifiers & (
            Qt.ControlModifier
            | Qt.ShiftModifier
            | Qt.AltModifier
        ):
            return

        item = self.item(row, column)

        if item is None:
            return

        if not (item.flags() & Qt.ItemIsEnabled):
            return

        if not (item.flags() & Qt.ItemIsEditable):
            return

        # Open the editor directly after the click.
        self.editItem(item)




    def fn_refresh_theme(self):

        self.setStyleSheet(fn_table_style())
        fn_apply_scrollbar_style(self)

        self._refresh_row_colors()
    