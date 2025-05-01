from __future__ import annotations

import os
from PySide6.QtGui import QIcon, QFont, QFontMetrics
from PySide6.QtCore import QModelIndex, Qt, QAbstractItemModel, QSize
from PySide6.QtWidgets import QStyle, QApplication

from csvpath.util.nos import Nos
from .treeitem import TreeItem


class TreeModel(QAbstractItemModel):

    def __init__(self, headers: list, data:Nos, parent=None, title:str="", sidebar=None):
        super().__init__(parent)
        self.root_data = [title]
        self.setHeaderData(value=title)
        self.root_item = TreeItem(data)
        self.setup_model_data(self.root_item)
        self.style = None
        self.sidebar = sidebar

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.root_data[0]
        return None

    def setHeaderData(self, section: int=0, orientation=Qt.Orientation.Horizontal, value="",
                      role=Qt.ItemDataRole.EditRole) -> bool:
        if role != Qt.ItemDataRole.EditRole or orientation != Qt.Orientation.Horizontal:
            return False

        self.root_data[0] = value
        self.headerDataChanged.emit(orientation,0,0)

        return True

    def set_style(self, style) -> None:
        self.style = style

    def columnCount(self, parent: QModelIndex = None) -> int:
        return 1

    def data(self, index: QModelIndex, role: int = None):
        if not index.isValid():
            return None
        if role == Qt.DecorationRole:
            pixmapi = None
            item = self.get_item(index)
            file = item.data(index.column()).isfile()
            if file is True:
                pixmapi = QStyle.StandardPixmap.SP_FileIcon
            else:
                pixmapi = QStyle.StandardPixmap.SP_DirLinkIcon
            icon = self.style.standardIcon(pixmapi)
            return icon

        if role == Qt.SizeHintRole:
            # Get the text for this item
            item = self.get_item(index)
            name = item.data(index.column()).path
            if name:
                name = os.path.basename(name)
                # Create a QFontMetrics object to measure text width
                font_metrics = QFontMetrics(QApplication.font())
                # Calculate the width needed for the text plus some padding
                text_width = font_metrics.horizontalAdvance(name) + 30  # Add padding
                # Return a size that's wide enough for the text
                size = QSize(text_width, 25)  # Height is fixed at 25, adjust as needed
                #
                # exp!
                #
                if self.sidebar:
                    if size.width() > self.sidebar.view.columnWidth(0):
                        self.sidebar.view.setColumnWidth(0, size.width())
                return size
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        item: TreeItem = self.get_item(index)
        name = item.data(index.column()).path
        name = os.path.basename(name)
        return name







    def filePath(self, index:QModelIndex):
        if not index.isValid():
            return None
        item: TreeItem = self.get_item(index)
        return item.data(index.column()).path

    def get_item(self, index: QModelIndex = QModelIndex()) -> TreeItem:
        if index.isValid():
            item: TreeItem = index.internalPointer()
            if item:
                return item
        return self.root_item

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if parent.isValid() and parent.column() != 0:
            return QModelIndex()
        parent_item: TreeItem = self.get_item(parent)
        if not parent_item:
            return QModelIndex()
        child_item: TreeItem = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        return QModelIndex()

    def parent(self, index: QModelIndex = QModelIndex()) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()
        child_item: TreeItem = self.get_item(index)
        if child_item:
            parent_item: TreeItem = child_item.parent()
        else:
            parent_item = None
        if parent_item == self.root_item or not parent_item:
            return QModelIndex()
        return self.createIndex(parent_item.child_number(), 0, parent_item)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid() and parent.column() > 0:
            return 0
        parent_item: TreeItem = self.get_item(parent)
        if not parent_item:
            return 0
        return parent_item.child_count()

    def setData(self, index: QModelIndex, value, role: int) -> bool:
        if role != Qt.ItemDataRole.EditRole:
            return False
        item: TreeItem = self.get_item(index)
        result: bool = item.set_data(index.column(), value)
        if result:
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
        return result

    def setup_model_data(self, parent: TreeItem):
        lst = parent.data(0).listdir()
        #
        # get the child_items in order to make it load its children
        #
        parent.child_items


    def _repr_recursion(self, item: TreeItem, indent: int = 0) -> str:
        result = " " * indent + repr(item) + "\n"
        for child in item.child_items:
            result += self._repr_recursion(child, indent + 2)
        return result

    def __repr__(self) -> str:
        return self._repr_recursion(self.root_item)
