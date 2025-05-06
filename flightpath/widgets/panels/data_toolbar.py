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

class DataToolbar(QToolBar):

    SMALL:int = 50
    MED:int = 250
    LARGE:int = 1000
    LARGER:int = 5000
    ALL_LINES = "All lines"

    FIRST_N = "First-n lines"
    RANDOM_0 = "Random from 0"
    RANDOM_ALL = "Random from all"

    QUOTES = "Quotes"
    SINGLE_QUOTES = "Single-quotes"

    COMMA = "Comma"
    TAB = "Tab"
    PIPE = "Pipe"
    SEMICOLON = "Semi-colon"


    def __init__(self, parent):
        super().__init__()

        self.parent = parent
        self.sampling = None
        self.rows = None
        self.save_sample = None
        self._setup()

    def _setup(self):
        self.parent.main.addToolBar(self)
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
        #
        # add sampling widgets
        #
        self.addWidget(self.rows)
        self.addWidget(self.sampling)
        self.addWidget(self.save_sample)
        #
        # add help
        #
        #self.toolbar_help = HelpLabel(main=self.parent.main, on_help=self.on_help_sample_toolbar)
        #self.toolbar.addWidget(self.toolbar_help)

        self.help = ClickableLabel()
        self.help.setStyleSheet("ClickableLabel { margin-left:5px;font-weight:100;color:#eeaa55;margin-right:20px; }")
        svg_renderer = QSvgRenderer(fiut.make_app_path(f"assets{os.sep}icons{os.sep}help.svg"))
        if not svg_renderer.isValid():
            print("Failed to load SVG file")
        pixmap = QPixmap(16,16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        svg_renderer.render(painter)
        painter.end()
        self.help.setPixmap(pixmap)
        self.addWidget(self.help)
        self.help.clicked.connect( self.on_help_sample_toolbar )
        #
        # delimiter
        #
        self.delimiter = QComboBox()
        self.delimiter.addItem(self.COMMA)
        self.delimiter.addItem(self.TAB)
        self.delimiter.addItem(self.PIPE)
        self.delimiter.addItem(self.SEMICOLON)
        self.addWidget(self.delimiter)
        #
        # quotechar
        #
        self.quotechar = QComboBox()
        self.quotechar.addItem(self.QUOTES)
        self.quotechar.addItem(self.SINGLE_QUOTES)
        self.addWidget(self.quotechar)





        #
        # let it move
        #
        self.setFloatable(True)
        self.setMovable(True)
        #
        # hide the toolbar till needed
        #
        self.hide()

    def delimiter_char(self) -> str:
        d = self.delimiter.currentText()
        if d == self.COMMA:
            return ","
        elif d == self.TAB:
            return "\t"
        elif d == self.PIPE:
            return "|"
        elif d == self.SEMICOLON:
            return ";"
        return None

    def quotechar_char(self) -> str:
        q = self.quotechar.currentText()
        if q == self.QUOTES:
            return '"'
        elif q == self.SINGLE_QUOTES:
            return "'"
        return None

    def on_help_sample_toolbar(self) -> None:
        md = HelpFinder(main=self.parent.main).help(f"data_view/samples.md")
        if md is None:
            self.parent.main.close_help()
            return
        self.parent.main.get_help_tab().setMarkdown(md)
        if not self.parent.main.is_showing_help():
            self.parent.main.on_click_help()


