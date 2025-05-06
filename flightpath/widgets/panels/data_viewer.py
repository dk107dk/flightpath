import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QTableView,
        QLabel,
)
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

from flightpath.util.style_utils import StyleUtility as stut
from .data_toolbar import DataToolbar

class DataViewer(QWidget):

    def __init__(self, parent):
        super().__init__()
        stut.set_common_style(self)
        self.parent = parent

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.table_view = QTableView()
        self.table_view.hide()

        layout.addWidget(self.label)
        layout.addWidget(self.table_view)
        layout.setContentsMargins(0, 0, 0, 0)

        self.toolbar = DataToolbar(parent=self.parent)


    def display_data(self, model):
        self.table_view.setModel(model)
        self.label.hide()
        self.table_view.show()
        self.toolbar.show()

    def clear(self, model):
        self.table_view.setModel(model)
        self.label.show()
        self.table_view.hide()
        self.toolbar.hide()


