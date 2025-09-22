import os

from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QTableView,
        QLabel,
        QAbstractItemView,
        QToolBar,
        QPushButton,
        QComboBox,
        QFrame
)

from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtGui import QColor, QPalette
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
        self.delimiter = None
        self.quotechar = None
        self._setup()

    def _setup(self):
        self.parent.addToolBar(self)
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
        #
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
        self._add_help(self.on_help_delimiter_toolbar)
        #
        # switch to raw source view
        #
        self.raw_source = QPushButton("Toggle raw source")
        self.addWidget(self.raw_source)
        self._add_help(self.on_help_raw_source_toolbar)
        #
        # switch to raw source view
        #
        self.file_info = QPushButton("File info")
        self.addWidget(self.file_info)
        #self._add_help(self.on_help_raw_source_toolbar)
        #
        # let it move
        #
        self.setFloatable(True)
        self.setMovable(True)
        #
        # hide the toolbar till needed
        #
        self.hide()

    def _add_help(self, callback) -> None:
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
        self.help.clicked.connect( callback )

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
            self.parent.helper.close_help()
            return
        self.parent.helper.get_help_tab().setMarkdown(md)
        if not self.parent.helper.is_showing_help():
            self.parent.helper.on_click_help()

    def on_help_delimiter_toolbar(self) -> None:
        md = HelpFinder(main=self.parent.main).help(f"data_view/delimiter.md")
        if md is None:
            self.parent.helper.close_help()
            return
        self.parent.helper.get_help_tab().setMarkdown(md)
        if not self.parent.helper.is_showing_help():
            self.parent.helper.on_click_help()

    def on_help_raw_source_toolbar(self) -> None:
        md = HelpFinder(main=self.parent.main).help(f"data_view/raw_source.md")
        if md is None:
            self.parent.helper.close_help()
            return
        self.parent.helper.get_help_tab().setMarkdown(md)
        if not self.parent.helper.is_showing_help():
            self.parent.helper.on_click_help()

    def disable(self) -> None:
        if self.sampling:
            self.sampling.setEnabled(False)
        if self.rows:
            self.rows.setEnabled(False)
        if self.save_sample:
            self.save_sample.setEnabled(False)
        if self.delimiter:
            self.delimiter.setEnabled(False)
        if self.quotechar:
            self.quotechar.setEnabled(False)
        if self.raw_source:
            self.raw_source.setEnabled(False)
        if self.file_info:
            self.file_info.setEnabled(False)

    def enable(self) -> None:
        if self.sampling:
            self.sampling.setEnabled(True)
        if self.rows:
            self.rows.setEnabled(True)
        if self.save_sample:
            self.save_sample.setEnabled(True)
        if self.delimiter:
            self.delimiter.setEnabled(True)
        if self.quotechar:
            self.quotechar.setEnabled(True)
        if self.raw_source:
            self.raw_source.setEnabled(True)
        if self.file_info:
            self.file_info.setEnabled(True)

