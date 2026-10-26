"""Bounded raw CAN presentation with lazy cell formatting and batched row changes."""
from PySide6.QtCore import QAbstractTableModel,QModelIndex,Qt
from PySide6.QtGui import QColor,QFontDatabase
from PySide6.QtWidgets import QTableView,QAbstractItemView,QHeaderView

from gui.themes.theme_manager import ThemeManager
from gui.themes.styles.controls.table_style import fn_table_style
from gui.themes.styles.controls.scrollbar_style import fn_apply_scrollbar_style


class CanMonitorModel(QAbstractTableModel):
    HEADERS=('Time (s)','Dir','CAN ID','DLC','Data (HEX)')

    def __init__(self,parent=None):
        super().__init__(parent)
        self.frames=[]
        self._mono_font=QFontDatabase.systemFont(QFontDatabase.FixedFont)

    def rowCount(self,parent=QModelIndex()): return 0 if parent.isValid() else len(self.frames)
    def columnCount(self,parent=QModelIndex()): return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(self,section,orientation,role=Qt.DisplayRole):
        if role==Qt.DisplayRole and orientation==Qt.Horizontal and 0<=section<len(self.HEADERS):
            return self.HEADERS[section]

    def data(self,index,role=Qt.DisplayRole):
        if not index.isValid() or not 0<=index.row()<len(self.frames): return None
        frame=self.frames[index.row()]
        if role==Qt.DisplayRole:
            return (f'{frame.timestamp_s:.6f}',frame.direction,
                f'{frame.can_id:08X}' if frame.is_extended_id else f'{frame.can_id:03X}',
                str(frame.dlc),frame.data.hex(' ').upper())[index.column()]
        if role==Qt.ToolTipRole:
            return (f'Wall timestamp: {frame.wall_timestamp_s} ({frame.timestamp_source})\n'
                f'Original driver stamp: {frame.source_timestamp_s}; source channel: {frame.source_channel}\n'
                f'Channel: {frame.channel}; extended: {frame.is_extended_id}\n'
                f'TX origin: {frame.tx_origin or "RX"}; echo of: {frame.echo_of_sequence}\n'
                f'Session: {frame.session_id}; sequence: {frame.sequence}')
        if role==Qt.FontRole and index.column()==4: return self._mono_font
        colors=ThemeManager.fn_colors()
        if role==Qt.BackgroundRole: return QColor(colors.TABLE_ROW if index.row()%2==0 else colors.TABLE_ROW_ALT)
        if role==Qt.ForegroundRole: return QColor(colors.TEXT)

    def set_frames(self,frames):
        frames=list(frames)
        overlap=0
        first=0
        if frames and self.frames:
            try:
                first=self.frames.index(frames[0])
                suffix=self.frames[first:]
                if frames[:len(suffix)]==suffix: overlap=len(suffix)
            except ValueError: pass
        if not overlap:
            self.beginResetModel();self.frames=frames;self.endResetModel()
            return
        if first:
            self.beginRemoveRows(QModelIndex(),0,first-1)
            del self.frames[:first]
            self.endRemoveRows()
        tail=frames[overlap:]
        if tail:
            self.beginInsertRows(QModelIndex(),len(self.frames),len(frames)-1)
            self.frames.extend(tail)
            self.endInsertRows()


class CanMonitorTable(QTableView):
    """QTableView styled from the same shared table/scrollbar rules as PrimaryTable."""
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setModel(CanMonitorModel(self))
        self.setSortingEnabled(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(30)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.fn_refresh_theme()

    def fn_refresh_theme(self):
        self.setStyleSheet(fn_table_style().replace('QTableWidget','QTableView'))
        fn_apply_scrollbar_style(self)
        model=self.model()
        if model.rowCount(): model.dataChanged.emit(model.index(0,0),model.index(model.rowCount()-1,4))
        self.viewport().update()
