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

class DataViewer(QWidget):

    def __init__(self, parent):
        super().__init__()
        stut.set_common_style(self)
        self.parent = parent

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.table_view = QTableView()
        self.table_view.hide()

        layout.addWidget(self.table_view)
        layout.setContentsMargins(0, 0, 0, 0)


    def display_data(self, model):
        self.table_view.setModel(model)
        self.table_view.show()
        self.parent.toolbar.show()

    def clear(self, model):
        self.table_view.setModel(model)
        self.table_view.hide()
        self.parent.toolbar.hide()


