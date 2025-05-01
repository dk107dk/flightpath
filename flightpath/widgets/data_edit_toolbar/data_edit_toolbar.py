from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
        QVBoxLayout,
        QLabel,
        QToolBar,
        QPushButton,
        QComboBox
)
from flightpath.util.style_utils import StyleUtility as stut

class DataEditToolbar(QToolBar):
    SMALL:int = 50
    MED:int = 250
    LARGE:int = 1000
    LARGER:int = 5000
    ALL_LINES = "All lines"

    FIRST_N = "First-n lines"
    RANDOM_0 = "Random from 0"
    RANDOM_ALL = "Random from all"


    def __init__(self, *, main, parent):
        super().__init__()
        self.parent = parent
        self.main = main

        self.sampling = None
        self.rows = None
        self.save_sample = None
        self._setup()

    def _setup(self):
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

        self.toolbar.setFloatable(True)
        self.toolbar.setMovable(True)
        self.toolbar.hide()



