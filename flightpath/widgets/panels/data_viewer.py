import os

from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QTableView,
        QLabel,
        QAbstractItemView,
        QToolBar,
        QPushButton,
        QComboBox
)

from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

from flightpath.widgets.clickable_label import ClickableLabel
from flightpath.util.help_finder import HelpFinder
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.style_utils import StyleUtility as stut

class DataViewer(QWidget):

    SMALL:int = 50
    MED:int = 250
    LARGE:int = 1000
    LARGER:int = 5000
    ALL_LINES = "All lines"

    FIRST_N = "First-n lines"
    RANDOM_0 = "Random from 0"
    RANDOM_ALL = "Random from all"


    def __init__(self, parent):
        super().__init__()
        stut.set_common_style(self)

        self.parent = parent
        self.sampling = None
        self.rows = None
        self.save_sample = None

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.table_view = QTableView()
        self.table_view.hide()

        layout.addWidget(self.label)
        layout.addWidget(self.table_view)
        layout.setContentsMargins(0, 0, 0, 0)

        self.toolbar = QToolBar("Sampling")
        self._setup_toolbar()



    def _setup_toolbar(self):
        self.parent.main.addToolBar(self.toolbar)
        self.save_sample = QPushButton("Save sample as")
        #
        # number of rows to show. we'll default to 50. should we find a way to save
        # the number for repeat openings?
        #
        self.rows = QComboBox()
        self.rows.addItem(str(self.SMALL))
        self.rows.addItem(str(self.MED))
        self.rows.addItem(str(self.LARGE))
        self.rows.addItem(str(self.LARGER))
        #
        # here all lines is a string. in the worker it is -1
        #
        self.rows.addItem(self.ALL_LINES)
        #
        # how should the lines be selected into the sample? again, should we save the setting?
        #
        self.sampling = QComboBox()
        self.sampling.addItem(self.FIRST_N)
        self.sampling.addItem(self.RANDOM_0)
        self.sampling.addItem(self.RANDOM_ALL)

        self.toolbar.addWidget(self.rows)
        self.toolbar.addWidget(self.sampling)
        self.toolbar.addWidget(self.save_sample)
        #
        # add help
        #
        #self.toolbar_help = HelpLabel(main=self.parent.main, on_help=self.on_help_sample_toolbar)
        #self.toolbar.addWidget(self.toolbar_help)

        self.help = ClickableLabel()
        self.help.setStyleSheet("ClickableLabel { margin-left:10px;font-weight:100;color:#eeaa55; }")
        svg_renderer = QSvgRenderer(fiut.make_app_path(f"assets{os.sep}icons{os.sep}help.svg"))
        if not svg_renderer.isValid():
            print("Failed to load SVG file")
        pixmap = QPixmap(16,16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        svg_renderer.render(painter)
        painter.end()
        self.help.setPixmap(pixmap)
        self.toolbar.addWidget(self.help)
        self.help.clicked.connect( self.on_help_sample_toolbar )


        #
        # let it move
        #
        self.toolbar.setFloatable(True)
        self.toolbar.setMovable(True)
        #
        # hide the toolbar till needed
        #
        self.toolbar.hide()

    def on_help_sample_toolbar(self) -> None:
        md = HelpFinder(main=self.parent.main).help(f"data_view/samples.md")
        if md is None:
            self.parent.main.close_help()
            return
        self.parent.main.get_help_tab().setMarkdown(md)
        self.parent.main.on_help_click()


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


