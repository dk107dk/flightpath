# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause
from __future__ import annotations

import json
import sys
from typing import Any
from PySide6.QtWidgets import QTreeView, QApplication, QHeaderView
from PySide6.QtCore import QAbstractItemModel, QModelIndex, QObject, Qt, QFileInfo
from .json_tree_item import TreeItem

class JsonModel(QAbstractItemModel):

    def __init__(self, parent: QObject = None, column_mode=2):
        super().__init__(parent)
        self._column_mode=column_mode
        self._rootItem = TreeItem()
        self._headers = ("key", "value")

    @property
    def headers(self) -> tuple[str]:
        return self._headers

    @headers.setter
    def headers(self, headers:tuple[str]) ->None:
        #
        # set two headers even if in column_mode=1. the second can be blank.
        # not digging into why because workaround.
        #
        self._headers = headers

    def clear(self):
        """ Clear data from the model """
        self.load({})

    def load(self, document: dict):
        assert isinstance(
            document, (dict, list, tuple)
        ), "`document` must be of dict, list or tuple, " f"not {type(document)}"

        self.beginResetModel()
        self._rootItem = TreeItem.load(document, column_mode=self._column_mode)
        self._rootItem.value_type = type(document)
        self.endResetModel()
        return True

    def data(self, index: QModelIndex, role: Qt.ItemDataRole) -> Any:
        if not index.isValid():
            return None
        item = index.internalPointer()
        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                return item.key
            if index.column() == 1:
                return item.value
        elif role == Qt.ItemDataRole.EditRole:
            if index.column() == 1:
                return item.value

    def setData(self, index: QModelIndex, value: Any, role: Qt.ItemDataRole):
        if role == Qt.ItemDataRole.EditRole:
            if index.column() == 1:
                item = index.internalPointer()
                item.value = str(value)
                self.dataChanged.emit(index, index, [Qt.ItemDataRole.EditRole])
                return True
        return False

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole
    ):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self._headers[section]

    def index(self, row: int, column: int, parent=QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        if not parent.isValid():
            parentItem = self._rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()
        childItem = index.internalPointer()
        parentItem = childItem.parent()
        if parentItem == self._rootItem:
            return QModelIndex()
        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent=QModelIndex()):
        if parent.column() > 0:
            return 0
        if not parent.isValid():
            parentItem = self._rootItem
        else:
            parentItem = parent.internalPointer()
        return parentItem.childCount()

    def columnCount(self, parent=QModelIndex()):
        # if column_mode 1 just show keys. list indexes are swapped out for list values.
        return self._column_mode

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super(JsonModel, self).flags(index)
        if index.column() == 1:
            return Qt.ItemFlag.ItemIsEditable | flags
        else:
            return flags

    def to_json(self, item=None):
        if item is None:
            item = self._rootItem
        nchild = item.childCount()
        if item.value_type is dict:
            document = {}
            for i in range(nchild):
                ch = item.child(i)
                document[ch.key] = self.to_json(ch)
            return document
        elif item.value_type == list:
            document = []
            for i in range(nchild):
                ch = item.child(i)
                document.append(self.to_json(ch))
            return document
        else:
            return item.value


