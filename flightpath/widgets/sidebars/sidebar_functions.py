import sys
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QPushButton,
    QWidget,
    QComboBox,
    QMenu,
    QMessageBox,
    QInputDialog,
    QVBoxLayout
)

from PySide6.QtGui import QPixmap, QIcon, QAction
from PySide6.QtCore import Qt, QSize, QModelIndex
from PySide6.QtWidgets import QFileSystemModel, QTreeView, QAbstractItemView, QSizePolicy, QHeaderView

from flightpath.widgets.clickable_label import ClickableLabel
from flightpath.widgets.json_tree_model.json_model import JsonModel
from flightpath.util.functions.function_collector import FunctionCollector

class SidebarFunctions(QWidget):

    FUNCTIONS = "Functions"
    MODES = "Modes"
    REFERENCES = "Reference types"
    KEYWORDS = "Keywords and symbols"
    RUNTIME = "Runtime print fields"
    QUALIFIERS = "Qualifiers"
    BUCKETS = None
    KEYWORD_NAMES = None

    def __init__(self, *, main):
        super().__init__()
        self.main = main
        self._docs = main.sidebar_docs
        if SidebarFunctions.BUCKETS is None:
            SidebarFunctions.BUCKETS = [
                SidebarFunctions.FUNCTIONS,
                SidebarFunctions.MODES,
                SidebarFunctions.REFERENCES,
                SidebarFunctions.KEYWORDS,
                SidebarFunctions.RUNTIME,
                SidebarFunctions.QUALIFIERS
            ]
        if SidebarFunctions.KEYWORD_NAMES is None:
            names = {}
            SidebarFunctions.KEYWORD_NAMES = names
            names["->"] = "when_do"
            names["=="] = "equals_equals"
            names["~"] = "tilde"
            names["$"] = "dollar"
            names["+"] = "plus"
            names["*"] = "star"
            names["\""] = "quotes"
            names["."] = "dot"
            names["'"] = "single_quotes"
            names["#"] = "hash"
            names["CSVPATH"] = "CSVPATH"
            names["ID/id"] = "ID"
            names["NAME/name"] = "NAME"
            names["PRINTOUT"] = "PRINTOUT"
            names["test-data"] = "test_data"
            names["test-delimiter"] = "test_delimiter"
            names["test-quotechar"] = "test_quotechar"

        self.setMinimumWidth(300)
        self.context_menu = None
        self.view = None
        self.model = None
        self._functions = None
        self.setup()
        self.function_name = None

    @property
    def docs(self):
        if self._docs is None:
            self._docs = self.main.sidebar_docs
        return self._docs

    @property
    def functions(self) -> FunctionCollector:
        if self._functions is None:
            self._functions = FunctionCollector()
        return self._functions

    def setup(self) -> None:
        layout = self.layout()
        if layout is None:
            layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.view = QTreeView()
        self.view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.view.setWordWrap(False)
        self.view.setAnimated(False)
        self.view.setAllColumnsShowFocus(True)
        self.view.setAutoScroll(True)
        self.view.setIndentation(10)
        self.view.setColumnWidth(0, 250)

        header = self.view.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        self.model = JsonModel(column_mode=1)
        self.model.headers = ("Help Topics", "")
        names = self.functions.function_names
        names = {
            SidebarFunctions.FUNCTIONS: names,
            SidebarFunctions.QUALIFIERS:[
                "asbool",
                "decrease",
                "distinct",
                "increase",
                "latch",
                "nocontrib",
                "notnone",
                "once",
                "onchange",
                "onmatch",
                "renew",
                "strict"
            ],
            SidebarFunctions.MODES:[
                "error-mode",
                "explain-mode",
                "files-mode",
                "logic-mode",
                "print-mode",
                "return-mode",
                "run-mode",
                "source-mode",
                "transfer-mode",
                "unmatched-mode",
                "validation-mode"
            ],
            SidebarFunctions.REFERENCES: [
                "csvpath",
                "csvpaths",
                "files",
                "headers",
                "metadata",
                "results",
                "variables"
            ],
            SidebarFunctions.KEYWORDS: SidebarFunctions.KEYWORD_NAMES,
            SidebarFunctions.RUNTIME: [
                "count_lines",
                "count_scans",
                "count_matches",
                "delimiter",
                "file_name",
                "headers",
                "identity",
                "last_line_time",
                "line_number",
                "lines_collected",
                "lines_time",
                "match_part",
                "quotechar",
                "run_started_at",
                "scan_part",
                "stopped",
                "total_lines",
                "valid"
            ]
        }
        self.model.load(names)

        self.view.setModel(self.model)
        self.view.updateGeometries()
        layout.addWidget(self.view)
        #
        # exp!
        #
        from flightpath.widgets.help.plus_help import HelpHeaderView
        self.view.setHeader(HelpHeaderView(self.view, on_help=self.main.helper.on_click_docs_help))
        self.view.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.view.header().setFixedHeight(24)
        self.view.header().setStyleSheet("QHeaderView {font-size:13px}")

        self.setLayout(layout)
        self.view.clicked.connect(self.on_functions_tree_click)

    def on_functions_tree_click(self, index) -> None:
        self.function_name = self.model.data(index, Qt.ItemDataRole.DisplayRole)
        if self.function_name is not None:
            i = self.model.parent(index)
            if i is None:
                return
            self.bucket_name = self.model.data(i, Qt.ItemDataRole.DisplayRole)
            if self.bucket_name is None:
                return
            if self.is_function(self.bucket_name, self.function_name):
                self.docs.display_function_for_name(self.bucket_name, self.function_name)
            else:
                self.docs.display_info(self.bucket_name, self.function_name)

    def is_function(self, bucket:str, name:str) -> bool:
        ret = bucket not in SidebarFunctions.BUCKETS
        return ret

    def refresh(self) -> None:
        if self.view:
            layout = self.layout()
            layout.removeWidget(self.view)
            self.view.deleteLater()
            self.setup()



