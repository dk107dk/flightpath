from PySide6 import QtCore

class DirectoryFilterProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None, excluded_dirs=None, *, sidebar):
        super().__init__(parent)
        self.excluded_dirs = excluded_dirs if excluded_dirs is not None else []
        self.sidebar = sidebar

    def filePath(self, index):
        source_index = self.mapToSource(index)
        if not source_index.isValid():
            return
        file_info = self.sidebar.file_model.fileInfo(source_index)
        return file_info.filePath()

    def filterAcceptsRow(self, source_row, source_parent):
        source_model = self.sourceModel()
        if not source_model:
            return True
        try:
            index = source_model.index(source_row, 0, source_parent)
            if not index.isValid():
                return False

            file_info = source_model.fileInfo(index)

            # Special case for root items
            if not source_parent.isValid():
                return True

            # Regular filtering
            if file_info.isDir():
                # Exclude directories in the list
                return file_info.fileName() not in self.excluded_dirs
            else:
                # Accept all non-directory files
                return True
        except Exception as e:
            print(f"Errorx!: e: {type(e)}: {e}: {source_model}")
            return False


    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        return super().data(index, role)

