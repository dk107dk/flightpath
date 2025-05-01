import sys

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPlainTextEdit,
    QLabel,
    QTreeView,
    QHeaderView,
    QSizePolicy
)

from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QFileInfo

from flightpath.util.style_utils import StyleUtility as stut
from flightpath.widgets.json_tree_model.json_model import JsonModel

class JsonSourceViewer(QWidget):

    def __init__(self, main):
        super().__init__()
        self.main = main
        stut.set_common_style(self)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.view = QTreeView()
        self.model = JsonModel()
        self.view.setModel(self.model)

        layout.addWidget(self.label)
        layout.addWidget(self.view)

    def open_file(self, *, path:str, data:str):
        info = QFileInfo(path)
        if not info.isFile() or info.suffix() != "json":
            self.label.show()
            self.view.hide()
            return
        self.model.load(data)

        self.label.hide()
        self.view.show()
        self.view.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.view.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.view.setAlternatingRowColors(True)

    def clear(self):
        self.label.show()
        self.view.hide()



