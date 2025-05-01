from PySide6.QtCore import Qt, QAbstractTableModel

class TableModel(QAbstractTableModel):
    def __init__(self, data=[]):
        super().__init__()
        self._data = data
        self._row_count = self._get_row_count()
        self._column_count = self._get_column_count()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return str(section)
        if role == Qt.DisplayRole and orientation == Qt.Vertical:
            return str(section)
        return super().headerData(section, orientation, role)

    def write_data(self, filepath):
        ...

    def _get_row_count(self):
        return len(self._data)

    def _get_column_count(self):
        try:
            return max(map(len, self._data))
        except ValueError:
            return 0

    def get_header_data(self):
        return self._data[0]

    def rowCount(self, parent=None):
        return self._row_count

    def columnCount(self, parent=None):
        return self._column_count

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

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return super().flags(index)

    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole:
            currentRow = self._data[index.row()]
            try:
                # if exists
                currentRow[index.column()] = value
            except IndexError:
                # else create empty cells
                currentRow += [None] * (index.column() - len(currentRow))
                currentRow.insert(index.column(), value)
            return True
        return False

