import sys
import json
import os
import traceback

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPlainTextEdit, QLabel, QMessageBox, QFileDialog, QTableView
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QFileInfo

from csvpath.util.file_readers import DataFileReader
from csvpath.util.metadata_parser import MetadataParser
from csvpath import CsvPath
from csvpath.util.printer import Printer
from csvpath.managers.errors.error_comms import ErrorCommunications
from csvpath.matching.util.expression_utility import ExpressionUtility as exut

from flightpath.util.style_utils import StyleUtility as stut
from flightpath.util.syntax_highlighter import CsvpathHighlighter
from flightpath.widgets.csvpath_text_edit import CsvPathTextEdit
from flightpath.util.printer import CapturePrinter
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.log_utility import LogUtility as lout
from flightpath.util.os_utility import OsUtility as osut
from flightpath.util.file_collector import FileCollector
from flightpath.widgets.simple_table_model import SimpleTableModel
from flightpath.widgets.panels.table_model import TableModel

class CsvpathSourceViewer(QWidget):
    CHAR_NAMES = {
        "pipe": "|",
        "bar": "|",
        "semi-colon": ";",
        "semicolon": ";",
        "comma": ",",
        "colon": ":",
        "hash":"#",
        "percent":"%",
        "star":"*",
        "asterisk":"*",
        "at":"@",
        "~":"tilde",
        "int": None,
        "quotes":'"',
        "quote": '"',
        "single-quotes":"'",
        "singlequotes":"'",
        "singlequote":"'",
        "single-quote":"'",
        "tick":"`"
        "tab":None
    }

    def __init__(self, main):

        super().__init__()
        self.main = main
        stut.set_common_style(self)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.saved = True
        self.mdata = None
        self._comment = None
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.text_edit = CsvPathTextEdit(main=main, parent=self)
        self.path = None
        self.text_edit.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.text_edit.setReadOnly(False)
        self.text_edit.setFont(QFont("Courier, monospace"))

        layout.addWidget(self.label)
        layout.addWidget(self.text_edit)
        layout.setContentsMargins(0, 0, 0, 0)

    def _statement_and_comment(self, csvpath:str) -> tuple[str,str]:
        mdatap = MetadataParser(None)
        cstr, comment = mdatap.extract_csvpath_and_comment(csvpath)
        cstr = cstr.strip()
        comment = comment.strip()
        return cstr, comment

    def _get_metadata(self, comment:str) -> None:
        if comment and self._comment != comment:
            print(f"comment not = comment")
            self._comment = None
            self.mdata = None
        if self.mdata is None and comment is not None:
            self._comment = comment
            mdatap = MetadataParser(None)
            self.mdata = {}
            mdatap._collect_metadata(self.mdata, comment)
        if self.mdata is None:
            self.mdata = {}
        return self.mdata

    def _get_filepath(self, cstr:str, comment:str) -> str:
        comment = "" if comment is None else comment.strip()
        mdata = {}
        if len(comment) > 0:
            mdata = self._get_metadata(comment)
        filepath = mdata.get("test-data")
        if filepath is None:
            return None
        filepath = filepath.strip()
        if not filepath.startswith("/"):
            #
            # check if we lopped off a leading '/'. metadata parser has a bug.
            # this is a stupid hack.  :/
            #
            i = comment.find(filepath)
            if i > 0 and comment[i-1] == '/':
                return f"/{filepath}"
        return filepath

    def _get_quotechar(self, comment:str=None) -> str:
        c = None
        mdata = self._get_metadata(comment)
        if mdata:
            c = mdata.get("test-quotechar")
            if c:
                c = self._get_char(c, '"')
        return c

    def _get_char(self, c:str, default:str) -> str:
        #
        # CsvPath does not support special characters in metadata. they are
        # allowed, but not preserved. that means we cannot assume test-delimiter
        # will just hold the actual delimiter char. we need to parse a char
        # name and use that to find the right delimiter char.
        #
        # we could do this a few ways. one approach would be to use the HTML
        # char codes (e.g. &nbsp;) but that feels hard for everyone. better to
        # just use "bar", "pipe", "semi-colon", "quotes", etc.
        #
        print(f"CsvpathSourceViewer: _get_char: c 1: {c}, default: {default}")
        if c == "int":
            try:
                c = chr(exut.to_int(c))
            except Exception:
                ...
        elif c == "tab":
            c = "\t"
        else:
            print(f"not int!")
            try:
                c = CsvpathSourceViewer.CHAR_NAMES.get(c)
            except Exception as e:
                print(f"e: {type(e)}: {e}")
                ...
        print(f"CsvpathSourceViewer: _get_char: c 2: {c}")
        if c is None:
            c = default
        c = c.strip()
        print(f"CsvpathSourceViewer: _get_char: c 3: {c}")
        return c

    def _get_delimiter(self, comment:str=None) -> str:
        c = None
        mdata = self._get_metadata(comment)
        print(f"CsvpathSourceViewer: _get_delimiter: mdata: {mdata}")
        if mdata:
            c = mdata.get("test-delimiter")
            print(f"_get_delimiter: c 1: >>{c}<<")
            if c:
                c = self._get_char(c, ",")
            print(f"_get_delimiter: c 2: {c}")
        return c

    def run_one_csvpath(self, csvpath:str, filepath:str=None) -> None:
        if (
            csvpath is None
            or csvpath.strip() == ""
            or csvpath.find("[") == -1
            or csvpath.find("$") == -1
        ):
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("No csvpath selected")
            msg_box.setText(f"Check that your cursor is in a csvpath statement")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
            return
        #
        #
        # we need to catch exceptions and display in error feedback panel
        #
        #
        cstr, comment = self._statement_and_comment(csvpath)
        if filepath is None:
            if cstr[1] == '[':
                filepath = self._get_filepath(cstr, comment)
            else:
                filepath = cstr[cstr.find("$")+1: cstr.find("[")]
        if filepath is None:
            #
            # request filename from user
            #
            filepath = FileCollector.select_file(
                parent=self,
                cwd=self.main.state.cwd,
                title="Select Data File",
                filter=FileCollector.csvs_filter(self.main.csvpath_config)
            )
            #
            # or, error message here.
            #
            ...
        # if we don't have the file in the cstr already add it
        if cstr.find(filepath) == -1:
            csvpath = f"~{comment}~ ${filepath}{cstr.lstrip('$')}"
        else:
            # otherwise, just add the comment back so we get the metadata
            csvpath = f"~{comment}~ {cstr}"
        lout.rotate_log(self.main.state.cwd, self.main.csvpath_config)
        quotechar = self._get_quotechar()
        delimiter = self._get_delimiter()
        #
        #
        #
        print(f"csvpath-source-view: run_one: quotechar: {quotechar}, delimiter: {delimiter}")
        path = CsvPath(quotechar=quotechar, delimiter=delimiter)
        lines = []
        capture = None
        try:
            path.parse(csvpath)
            path.logger.info("starting one-off run")
            path.update_settings_from_metadata()
            path.ecoms = ErrorCommunications(csvpath=path)
            #
            # setup a printer to capture output
            #
            capture = CapturePrinter()
            path.set_printers([capture])
            lines = path.collect()
        except Exception as e:
            estr = traceback.format_exc()
            self._display_stacktrace(estr)
            return
        #
        # shut down the logger. not sure this is needed, but ruling stuff out.
        #
        lout.clear_logging(path)
        #
        # display to the user in the lower panel
        #
        self._run_feedback(csvpath_str=csvpath, path=path, lines=lines, printer=capture)
        #
        # there's no absolute need to drop the metadata, but it seems prudent
        #
        self.mdata = None

    def _display_stacktrace(self, trace:str) -> None:
        self._clear_feedback()
        es = QWidget()
        es.setObjectName("Error")
        self.main.help_and_feedback.addTab(es, "Error")
        layout = QVBoxLayout()
        es.setLayout(layout)
        ev = QPlainTextEdit()
        ev.setPlainText(trace)
        ev.setReadOnly(True)
        layout.addWidget(ev)
        layout.setContentsMargins(0, 0, 0, 0)
        self.main.help_and_feedback.setCurrentWidget(es)
        self.main.help_and_feedback.show()
        if not self.main.is_showing_help():
            self.main.on_click_help()

    def _clear_feedback(self) -> None:
        while self.main.help_and_feedback.count() > 0:
            t = self.main.help_and_feedback.widget(0)
            self.main.help_and_feedback.removeTab(0)
            t.deleteLater()

    def _run_feedback(self, *, csvpath_str, path:CsvPath, lines:list, printer:Printer) -> None:
        #
        # remove all tabs (not incl. help)
        #
        self._clear_feedback()
        printouts_label = "Printouts - default"
        helptab = None
        #
        # create new tabs
        #
        #
        # we don't know how many tabs we have (>=1) so do them first iteratively
        #
        for name in printer.names:
            printout = printer.to_string(name)
            default = QWidget()
            printer_name = f"Printouts - {name}"
            default.setObjectName(printer_name)
            self.main.help_and_feedback.addTab(default, printer_name)

            print_layout = QVBoxLayout()
            default.setLayout(print_layout)
            print_view = QPlainTextEdit()
            printout = printer.to_string(name)
            print_view.setPlainText(printout)
            print_view.setReadOnly(True)
            print_layout.addWidget(print_view)
            print_layout.setContentsMargins(0, 0, 0, 0)

        log = QWidget()
        log.setObjectName("Log")
        self.main.help_and_feedback.addTab(log, "Log")

        errors = QWidget()
        errors.setObjectName("Errors")
        self.main.help_and_feedback.addTab(errors, "Errors")

        matches = QWidget()
        matches.setObjectName("Matches")
        self.main.help_and_feedback.addTab(matches, "Matches")

        variables = QWidget()
        variables.setObjectName("Variables")
        self.main.help_and_feedback.addTab(variables, "Variables")

        code = QWidget()
        code.setObjectName("Code")
        self.main.help_and_feedback.addTab(code, "Automation code")
        #
        # get the log
        #
        log_lines = lout.get_log_content(self.main.csvpath_config)
        #
        # display data in each tab
        #
        self._display_log(log, log_lines )
        self._display_errors(errors, path.errors )
        self._display_code(code, csvpath_str)
        self._display_matches(matches, lines)
        self._display_variables(variables, path.variables)
        #
        # this name obviously isn't general enough, but it pops open the bottom panel.
        #
        if not self.main.is_showing_help():
            self.main.on_click_help()
        t = self.main.help_and_feedback.findChild(QWidget, printouts_label)
        self.main.help_and_feedback.setCurrentWidget(t)
        self.main.help_and_feedback.show()

    def _display_log(self, log:QWidget, log_lines:str) -> None:
        layout = QVBoxLayout()
        log.setLayout(layout)
        view = QPlainTextEdit()
        view.setPlainText(log_lines)
        view.setReadOnly(True)
        layout.addWidget(view)
        layout.setContentsMargins(0, 0, 0, 0)

    def _display_matches(self, matches:QWidget, lines:list[list[str]]) -> None:
        layout = QVBoxLayout()
        matches.setLayout(layout)
        matches_view = QTableView()
        model = TableModel(lines)
        #model = SimpleTableModel(lines)
        matches_view.setModel(model)
        layout.addWidget(matches_view)
        layout.setContentsMargins(0, 0, 0, 0)

    def _display_code(self, code:QWidget, csvpath_str:str) -> None:
        pseudo = f"""
~ for a one-off validation ~
from csvpath import CsvPath
path = CsvPath(
                       '''{csvpath_str}''')
lines = path.collect()
"""
        layout = QVBoxLayout()
        code.setLayout(layout)
        code_view = QPlainTextEdit()
        code_view.setPlainText(pseudo)
        code_view.setReadOnly(True)
        layout.addWidget(code_view)
        layout.setContentsMargins(0, 0, 0, 0)

    def _display_errors(self, errors:QWidget, es:list) -> None:
        es = [e.to_json() for e in es]
        layout = QVBoxLayout()
        errors.setLayout(layout)
        errors_view = QPlainTextEdit()
        errors_str = json.dumps(es, indent=2)
        errors_view.setPlainText(errors_str)
        errors_view.setReadOnly(True)
        layout.addWidget(errors_view)
        layout.setContentsMargins(0, 0, 0, 0)

    def _display_variables(self, variables:QWidget, vdata:dict) -> None:
        layout = QVBoxLayout()
        variables.setLayout(layout)
        variables_view = QPlainTextEdit()
        variables_str = json.dumps(vdata, indent=2)
        variables_view.setPlainText(variables_str)
        variables_view.setReadOnly(True)
        layout.addWidget(variables_view)
        layout.setContentsMargins(0, 0, 0, 0)

    def _clear_tab(self, tab) -> None:
        #
        # TODO: remove
        # we're clearing each tab, but we probably don't benefit.
        # this approach predated just deleting all the tabs and
        # recreating.
        #
        #
        layout = tab.layout()
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                if item:
                    w = item.widget()
                    if w:
                        w.deleteLater()
            layout.deleteLater()

    def reset_saved(self) -> None:
        self.saved = True
        i = self.main.content.tab_widget.currentIndex()
        name = self.main.content.tab_widget.tabText(i)
        name = name.replace("+", "")
        self.main.content.tab_widget.setTabText(i, name )


    def open_file(self, *, path:str, data:str) -> None:
        self.path = path
        info = QFileInfo(path)
        if not info.isFile() or not info.suffix() in self.main.csvpath_config.csvpath_file_extensions:
            self.label.show()
            self.text_edit.hide()
            return
        self.text_edit.clear()
        #
        # internal operations can pass None in some cases. e.g. copying.
        #
        if data is None:
            with DataFileReader(path) as file:
                data = file.source.read()

        self.label.hide()
        #highlighter = CsvpathHighlighter(self.text_edit.document())

        from flightpath.util.highlighters import MultiHighlighter, CommentHighlighter
        multi = MultiHighlighter(self.text_edit.document())
        highlighter = CsvpathHighlighter(None, parent=multi)
        highlighters = [highlighter, CommentHighlighter(None, parent=multi) ]
        multi.highlighters = highlighters

        self.text_edit.show()
        self.text_edit.setPlainText(data)
        c = "cmd" if osut.is_mac() else "ctrl"
        self.main.statusBar().showMessage(f"{c}-s to save, {c}-r to run • Opened {path}")
        self.main.content.set_csvpath_tab_name( os.path.basename(path) )


    def clear(self):
        #self.label.show()
        self.text_edit.hide()
        self.path = None



