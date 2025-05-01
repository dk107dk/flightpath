# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause
from __future__ import annotations

import json
import sys
from typing import Any
from PySide6.QtCore import Qt


class TreeItem:

    def __init__(self, parent: "TreeItem" = None):
        self._parent = parent
        self._key = ""
        self._value = ""
        self._value_type = None
        self._children = []

    def appendChild(self, item: "TreeItem"):
        """Add item as a child"""
        self._children.append(item)

    def child(self, row: int) -> "TreeItem":
        """Return the child of the current item from the given row"""
        return self._children[row]

    def parent(self) -> "TreeItem":
        """Return the parent of the current item"""
        return self._parent

    def childCount(self) -> int:
        """Return the number of children of the current item"""
        return len(self._children)

    def row(self) -> int:
        """Return the row where the current item occupies in the parent"""
        return self._parent._children.index(self) if self._parent else 0

    @property
    def key(self) -> str:
        """Return the key name"""
        return self._key

    @key.setter
    def key(self, key: str):
        """Set key name of the current item"""
        self._key = key

    @property
    def value(self) -> str:
        """Return the value name of the current item"""
        return self._value

    @value.setter
    def value(self, value: str):
        """Set value name of the current item"""
        self._value = value

    @property
    def value_type(self):
        """Return the python type of the item's value."""
        return self._value_type

    @value_type.setter
    def value_type(self, value):
        """Set the python type of the item's value."""
        self._value_type = value

    @classmethod
    def load(
        cls, value: list | dict, parent: "TreeItem" = None, sort=True, column_mode=2
    ) -> "TreeItem":
        rootItem = TreeItem(parent)
        rootItem.key = "root"
        if isinstance(value, dict):
            items = sorted(value.items()) if sort else value.items()
            for key, value in items:
                child = cls.load(value, rootItem, column_mode=column_mode)
                child.key = key
                child.value_type = type(value)
                rootItem.appendChild(child)
        elif isinstance(value, list):
            if column_mode == 1:
                #
                # single column
                #
                for index, value in enumerate(value):
                    child = cls.load(value, rootItem, column_mode=column_mode)
                    child.key = value
                    child.value_type = type(value)
                    rootItem.appendChild(child)
            else:
                for index, value in enumerate(value):
                    child = cls.load(value, rootItem, column_mode=column_mode)
                    child.key = index
                    child.value_type = type(value)
                    rootItem.appendChild(child)
        else:
            rootItem.value = value
            rootItem.value_type = type(value)
        return rootItem


