import json
import os

import darkdetect
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QFormLayout,
        QLabel,
        QSizePolicy,
        QTextEdit
)
from PySide6.QtCore import Qt
from csvpath.matching.functions.function import Function
from csvpath.util.nos import Nos

from flightpath.util.functions.function_collector import FunctionCollector
from flightpath.util.functions.function_parts import FunctionParts
from flightpath.util.html_generator import HtmlGenerator
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.widgets.sidebars.sidebar_functions import SidebarFunctions

class SidebarDocs(QWidget):

    def __init__(self, *, main, functions:FunctionCollector=None):
        super().__init__()
        self.main = main
        self.setMinimumWidth(300)
        self.context_menu = None
        self._function_collector = functions if functions is not None else FunctionCollector()
        self.setStyleSheet("font-size: 13px; padding: 0px;")
        self._description = None
        self.setup()

    @property
    def description(self) -> QTextEdit:
        if self._description is None:
            self._description = QTextEdit()
            self._description.setReadOnly(True)
            self._description.setText("")
            s = "QTextEdit {"
            s = f"{s}background-color:#{'#494949' if darkdetect.isDark() else 'fff'}"
            s = s + ";}"
            self._description.setStyleSheet(s)
        return self._description

    @description.setter
    def description(self, d:QTextEdit) -> QTextEdit:
        self._description = d

    @property
    def functions_collector(self) -> FunctionCollector:
        if self._function_collector is None:
            self._function_collector = FunctionCollector()
        return self._function_collector

    def setup(self) -> None:
        layout = self.layout()
        if layout is None:
            layout = QVBoxLayout()
            layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0,0,0)

        self.label_top = QLabel()
        self.label_top.setText("Help Info")
        self.label_top.setStyleSheet("""
            QLabel {
                border-bottom:1px solid #aaa;
                font-weight:600;
        }""")
        #
        # display all the parts
        #
        layout.addWidget(self.label_top)
        layout.addWidget(self.description)
        self.setLayout(layout)

    def display_function_for_name(self, bucket_name:str, function_name:str) -> None:
        functions = self.functions_collector.functions
        bucket = functions.get(bucket_name)
        function = bucket.get(function_name)
        if function:
            self.display_function(function)

    def display_function(self, function:Function) -> None:
        function_json = FunctionParts.describe(function)
        html = self._generate_html(function_json)
        self.description.setText( html )

    def _generate_html(self, f:dict) -> str:
        path = fiut.make_app_path(f"assets{os.sep}help{os.sep}templates{os.sep}function_description.html")
        #
        # add indication of light / dark mode so we can adjust colors
        #
        f["ui_dark"] = darkdetect.isDark()
        #
        #
        #
        html = HtmlGenerator.load_and_transform(path, f)
        return html

    def display_info(self, bucket_name:str, name:str ) -> None:
        html = None
        bucket_name = bucket_name.replace(" ", "_")
        if name in SidebarFunctions.KEYWORD_NAMES:
            name = SidebarFunctions.KEYWORD_NAMES.get(name)
        name = name.lower()
        bucket_name = bucket_name.lower()
        path = fiut.make_app_path(f"assets{os.sep}help{os.sep}{bucket_name}{os.sep}{name}.html")

        self.main.log(f"DocsSidebar: template path: {path}")

        f = {}
        f["ui_dark"] = darkdetect.isDark()
        #
        #
        #
        if path is None:
            #
            # if we have no path we should fail early. we fail silently because there are times
            # when we don't have content to show, but don't want an error state.
            #
            print(f"Warning: no path to content in HtmlGenerator.display_info")
            return
        raw = HtmlGenerator.load_and_transform(path, f)
        html = ""
        styles = ""
        for _ in raw.split("<code>"):
            a = ""
            b = ""
            if _.find("</code>"):
                s = _.split("</code>")
                a = s[0]
                b = s[1] if len(s) > 1 else ""
                if b == "":
                    html = f"{html}{a}"
                else:
                    lexer = get_lexer_by_name("xquery", stripall=True)
                    formatter = HtmlFormatter()
                    a = highlight(a, lexer, formatter)
                    if styles == "":
                        styles = formatter.get_style_defs('.highlight')
                        html = f"{html}<style>{styles}</style>"
                    html = f"{html}<div class='code'>{a}</div>{b}"
            else:
                html = f"{html}{a}"
        self.description.setText( html )

    def refresh(self) -> None:
        if self.view:
            layout = self.layout()  # Get the existing layout
            layout.removeWidget(self.view)
            self.view.deleteLater()  # Delete the old widget
            self.setup()

