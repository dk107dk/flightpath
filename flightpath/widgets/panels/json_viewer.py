import sys

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTreeView,
    QHeaderView,
    QSizePolicy
)

from PySide6.QtCore import Qt, QFileInfo

from flightpath.util.style_utils import StyleUtility as stut
from flightpath.widgets.json_tree_model.json_model import JsonModel

class JsonViewer(QWidget):

    def __init__(self, main):
        super().__init__()
        self.main = main
        stut.set_common_style(self)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.view = QTreeView()
        self.model = JsonModel()
        self.view.setModel(self.model)
        layout.addWidget(self.view)

    def open_file(self, *, path:str, data:str):
        info = QFileInfo(path)
        if not info.isFile() or info.suffix() != "json":
            self.view.hide()
            return
        self.model.load(data)
        self.view.show()
        self.view.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.view.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.view.setAlternatingRowColors(True)

    def clear(self):
        self.view.hide()



