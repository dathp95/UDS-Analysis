from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QAbstractItemView, QTableView

from gui.themes.styles.controls.scrollbar_style import fn_apply_scrollbar_style
from gui.themes.styles.controls.table_style import fn_table_style
from gui.themes.theme_manager import ThemeManager


class QCurrentReviewModel(QAbstractTableModel):
    HEADERS = ("No.", "Time", "Current (mA)")
    BATCH_SIZE = 512

    def __init__(self, parent=None):
        super().__init__(parent)
        self.samples = []
        self._visible_count = 0

    def set_samples(self, samples):
        self.beginResetModel()
        self.samples = samples
        self._visible_count = min(len(samples), self.BATCH_SIZE)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else self._visible_count

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.HEADERS)

    def canFetchMore(self, parent=QModelIndex()):
        return not parent.isValid() and self._visible_count < len(self.samples)

    def fetchMore(self, parent=QModelIndex()):
        if not self.canFetchMore(parent):
            return
        count = min(self.BATCH_SIZE, len(self.samples) - self._visible_count)
        self.beginInsertRows(QModelIndex(), self._visible_count, self._visible_count + count - 1)
        self._visible_count += count
        self.endInsertRows()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal and 0 <= section < len(self.HEADERS):
            return self.HEADERS[section]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < self._visible_count:
            return None
        row, column = index.row(), index.column()
        sample = self.samples[row]
        if role == Qt.DisplayRole:
            if column == 0:
                return str(row + 1)
            if column == 1:
                return str(sample.time)
            if column == 2:
                return f"{sample.current_mA:.2f}"
        elif role == Qt.TextAlignmentRole:
            return (Qt.AlignCenter if column == 0 else
                    Qt.AlignRight | Qt.AlignVCenter if column == 2 else
                    Qt.AlignLeft | Qt.AlignVCenter)
        elif role == Qt.BackgroundRole:
            colors = ThemeManager.fn_colors()
            return QColor(colors.TABLE_ROW if row % 2 == 0 else colors.TABLE_ROW_ALT)
        return None


class QCurrentReviewTable(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalHeader().hide()
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setResizeContentsPrecision(100)
        self.fn_refresh_theme()

    def focusOutEvent(self, event):
        self.clearSelection()
        self.setCurrentIndex(QModelIndex())
        super().focusOutEvent(event)

    def fn_refresh_theme(self):
        self.setStyleSheet(fn_table_style().replace("QTableWidget", "QTableView"))
        fn_apply_scrollbar_style(self)
        self.viewport().update()
