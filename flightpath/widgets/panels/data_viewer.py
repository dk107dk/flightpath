import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QStackedLayout,
        QTableView,
        QLabel,
)
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

from flightpath.util.style_utils import StyleUtility as stut

from .raw_viewer import RawViewer

class DataViewer(QWidget):

    def __init__(self, parent):
        super().__init__()
        #
        # sets the font size
        #
        stut.set_common_style(self)
        #
        #
        #
        self.parent = parent
        self.main = parent.main
        self.path = self.main.selected_file_path
        self.main_layout = QStackedLayout()
        self.setLayout(self.main_layout)
        self.table_view = QTableView()
        self.table_view.hide()
        self.raw_view = RawViewer(self.main)
        self.main_layout.addWidget(self.table_view)
        self.main_layout.addWidget(self.raw_view)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        #
        # the list of int representing the lines we display. the
        # raw viewer needs the same lines
        #
        self.lines_to_take = None

    def toggle_grid_raw(self):
        i = self.layout().currentIndex()
        i = 0 if i == 1 else 1
        w = self.layout().widget(1)
        if i == 1 and w.loaded == False:
            w.open_file(self.main.selected_file_path, self.lines_to_take)
        self.layout().setCurrentIndex(i)

    def display_data(self, model):
        self.table_view.setModel(model)
        self.table_view.show()
        self.parent.toolbar.show()
        self.layout().setCurrentIndex(0)

    def clear(self, model):
        self.table_view.setModel(model)
        self.table_view.hide()
        self.parent.toolbar.hide()
        self.layout().setCurrentIndex(0)

