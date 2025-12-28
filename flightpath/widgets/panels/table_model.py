from PySide6.QtCore import Qt, QAbstractTableModel, Signal, QModelIndex
from .viewer_signals import ViewerSignals

class TableModel(QAbstractTableModel):
    def __init__(self, *, data=None, editable=False):
        if data is None:
            data = []
        super().__init__()
        self._data = data
        self._editable = editable
        #self._column_count = self._get_column_count()
        self.signals = ViewerSignals()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return str(section)
        if role == Qt.DisplayRole and orientation == Qt.Vertical:
            return str(section)
        return super().headerData(section, orientation, role)

    def write_data(self, filepath):
        ...

    def insertRows(self, row, count=1, new_row_data=None, parent=QModelIndex()):
        if parent.isValid():
            return False  # Not applicable for a flat table model
        if new_row_data is None:
            num_cols = self.columnCount() if self.rowCount() > 0 else 0
            new_row_data = [''] * num_cols
        self.beginInsertRows(parent, row, row + count - 1)
        for i in range(count):
            self._data.insert(row + i, new_row_data.copy())
        self.endInsertRows()
        self.signals.rows_inserted.emit( (row, count) )
        return True

    def insertColumns(self, column, count=1, parent=QModelIndex()):
        if parent.isValid():
             return False
        self.beginInsertColumns(parent, column, column + count - 1)
        for row_data in self._data:
            for i in range(count):
                row_data.insert(column + i, "")
        self.endInsertColumns()
        self.signals.columns_inserted.emit( (column, count) )
        return True

    def remove_columns(self, column: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        if parent.isValid():
            return False
        if column < 0 or column + count > self.columnCount():
            return False
        self.beginRemoveColumns(parent, column, column + count - 1)
        for row_data in self._data:
            del row_data[column : column + count]
        self.endRemoveColumns()
        self.signals.columns_deleted.emit( (column, count) )
        return True

    def remove_rows(self, row: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        if parent.isValid():
            return False
        # Check if the requested rows are within the valid range
        if row < 0 or row + count > self.rowCount():
            return False

        # The range is inclusive, so it's `row + count - 1`
        self.beginRemoveRows(parent, row, row + count - 1)

        del self._data[row : row + count]

        self.endRemoveRows()
        self.signals.rows_deleted.emit( (row, count) )
        # self.dataModified.emit() # Optional: signal for save state
        return True




    """
    def _get_row_count(self):
        try:
            return len(self._data)
        except:
            return 0
    """

    def _get_column_count(self):
        try:
            return max(map(len, self._data))
        except ValueError:
            return 0

    def get_header_data(self):
        return self._data[0]

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return self._get_column_count()

    def get_data(self) -> list:
        return self._data

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            try:
                value = self._data[index.row()][index.column()]
            except IndexError:
                return None
            return value

    """
    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable
    """
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        default_flags = super().flags(index)
        if not index.isValid():
            return default_flags
        if self._editable:
            return default_flags | Qt.ItemFlag.ItemIsEditable
        #
        # return default flags -- allows the item to be selected (and copied), not edited
        #
        return default_flags


    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole:
            currentRow = self._data[index.row()]
            currentValue = None
            try:
                currentValue = currentRow[index.column()]
                # if exists
                if currentValue != value:
                    currentRow[index.column()] = value
            except IndexError:
                # else create empty cells
                currentRow += [None] * (index.column() - len(currentRow))
                currentRow.insert(index.column(), value)
            #
            # emit edit event
            #
            self.dataChanged.emit(index, index)
            self.signals.edit_made.emit((index.row(), index.column(), currentValue, value))
            return True
        return False




