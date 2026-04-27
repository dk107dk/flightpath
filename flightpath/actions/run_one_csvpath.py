import json
import os
import traceback

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPlainTextEdit,
    QTextEdit,
    QMessageBox,
)
from PySide6.QtGui import QFontDatabase
from PySide6.QtCore import Slot

from csvpath import CsvPath
from csvpath.managers.errors.error_comms import ErrorCommunications
from csvpath.util.printer import Printer

from flightpath.widgets.table_model import TableModel

from flightpath.widgets.panels.json_viewer import JsonViewer
from flightpath.widgets.panels.raw_viewer import RawViewer
from flightpath.widgets.panels.data_viewer import DataViewer

from flightpath.workers.one_off_run import OneOffRunWorker
from flightpath.util.printer import CapturePrinter
from flightpath.util.run_info import RunInfo
from flightpath.util.file_collector import FileCollector
from flightpath.util.html_generator import HtmlGenerator
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.log_utility import LogUtility as lout
from flightpath.util.message_utility import MessageUtility as meut
from flightpath.util.csvpath_utility import CsvpathUtility as csut
from flightpath.util.editable import EditStates


class RunOneCsvpath:
    def __init__(self, *, main):
        super().__init__()
        self.main = main
        #
        # this class is long-lived. that means this worker reference
        # may be reused. we don't really care about that since we only need it
        # for as long as it takes to run and display results.
        #
        self.workers = []

    # ==================================

    def _get_filepath(self, csvpath: str) -> str:
        if (
            csvpath is None
            or csvpath.strip() == ""
            or csvpath.find("[") == -1
            or csvpath.find("$") == -1
        ):
            meut.message2(
                parent=self.main,
                msg="Check that your cursor is in a csvpath statement",
                title="No csvpath selected",
            )
            return False
        #
        #
        # we need to catch exceptions and display in error feedback panel
        #
        #
        cstr, comment = csut.statement_and_comment(csvpath)
        filepath = None
        if cstr[1] == "[":
            filepath = csut.get_filepath(comment)
        else:
            filepath = cstr[cstr.find("$") + 1 : cstr.find("[")]
        return filepath

    def run_one_csvpath(
        self, csvpath: str, filepath: str = None, *, position=None
    ) -> None:
        filepath = self._get_filepath(csvpath)
        if filepath is False:
            return
        if filepath is None:
            filepath = FileCollector.select_file(
                parent=self,
                cwd=self.main.state.cwd,
                title="Select Data File",
                file_type_filter=FileCollector.csvs_filter(self.main.csvpath_config),
                callback=self.run_one_csvpath_2,
                args={"csvpath": csvpath, "position": position},
            )
            return
        self.run_one_csvpath_2(filepath, csvpath=csvpath, position=position)

    def run_one_csvpath_2(self, filepath, *, csvpath: str, position=None) -> None:
        if filepath is None:
            meut.message2(
                parent=self.main,
                title="No File",
                msg="No file was selected. Cannot continue.",
            )
            return
        #
        cstr, comment = csut.statement_and_comment(csvpath)
        #
        if "test-data:" not in comment:
            self.text_edit.add_to_external_comment_of_csvpath_at_position(
                position=position, addto=f"test-data:{filepath}\n"
            )
        #
        if cstr.find(filepath) == -1:
            csvpath = f"~{comment}~ ${filepath}{cstr.lstrip('$')}"
        else:
            # otherwise, just add the comment back so we get the metadata
            csvpath = f"~{comment}~ {cstr}"
        #
        lout.rotate_log(self.main.state.cwd, self.main.csvpath_config)
        quotechar = csut.get_quotechar(comment)
        delimiter = csut.get_delimiter(comment)
        #
        # this will blowup until the next CsvPaths release
        #
        # path = CsvPath(quotechar=quotechar, delimiter=delimiter)
        try:
            path = CsvPath(
                quotechar=quotechar,
                delimiter=delimiter,
                project=self.main.state.current_project,
                project_context="FlightPath Data",
            )
            path.parse(csvpath)
            size = os.path.getsize(filepath)
            if size >= 1000000:
                meut.yesNo2(
                    parent=self.main,
                    msg="Development goes faster with smaller samples. Stop to create a sample?",
                    title="Large file",
                    callback=self._do_run_one_csvpath,
                    args={
                        "path": path,
                        "filename": path.scanner.filename,
                        "csvpath": csvpath,
                    },
                )
                return
            else:
                self._do_run_one_csvpath(
                    QMessageBox.No, path=path, csvpath=csvpath, filename=filepath
                )
        except Exception as e:
            estr = traceback.format_exc()
            self._display_stacktrace(estr)
            meut.warning2(parent=self.main, title="Error", msg=f"Error: {e}")

    """
    def run_one_csvpath( self, csvpath: str, filepath: str = None, *, position=None) -> None:
        if (
            csvpath is None
            or csvpath.strip() == ""
            or csvpath.find("[") == -1
            or csvpath.find("$") == -1
        ):
            meut.message2(
                parent=self.main,
                msg="Check that your cursor is in a csvpath statement",
                title="No csvpath selected",
            )
            return
        #
        #
        # we need to catch exceptions and display in error feedback panel
        #
        #
        cstr, comment = csut.statement_and_comment(csvpath)
        if filepath is None:
            if cstr[1] == "[":
                filepath = csut.get_filepath(comment)
            else:
                filepath = cstr[cstr.find("$") + 1 : cstr.find("[")]
        if comment is None:
            #
            # not sure this would happen, but we can defend
            #
            comment = ""
        comment = comment.strip()
        if filepath is None:
            #
            # request filename from user
            #
            filepath = FileCollector.select_file(
                parent=self,
                cwd=self.main.state.cwd,
                title="Select Data File",
                file_type_filter=FileCollector.csvs_filter(self.main.csvpath_config),
            )
            #
            # or, error message here.
            #
    #
    # -----------------------------
    #
            if filepath is None:
                meut.message2(
                    parent=self.main,
                    title="No File",
                    msg="No file was selected. Cannot continue.",
                )
                return
            #
            # add the test data file to the comment. easy to add to comment, but how to
            # get it back into the original file....
            #
            self.text_edit.add_to_external_comment_of_csvpath_at_position(
                position=position, addto=f"test-data:{filepath}\n"
            )
            #
            #
            #
        # if we don't have the file in the cstr already add it
        if cstr.find(filepath) == -1:
            csvpath = f"~{comment}~ ${filepath}{cstr.lstrip('$')}"
        else:
            # otherwise, just add the comment back so we get the metadata
            csvpath = f"~{comment}~ {cstr}"
        lout.rotate_log(self.main.state.cwd, self.main.csvpath_config)
        quotechar = csut.get_quotechar(comment)
        delimiter = csut.get_delimiter(comment)
        #
        # this will blowup until the next CsvPaths release
        #
        # path = CsvPath(quotechar=quotechar, delimiter=delimiter)
        try:
            path = CsvPath(
                quotechar=quotechar,
                delimiter=delimiter,
                project=self.main.state.current_project,
                project_context="FlightPath Data",
            )
            path.parse(csvpath)
            size = os.path.getsize(filepath)
            if size >= 1000000:
                meut.yesNo2(
                    parent=self.main,
                    msg="Development goes faster with smaller samples. Stop to create a sample?",
                    title="Large file",
                    callback=self._do_run_one_csvpath,
                    args={"path":path, "filename":path.scanner.filename, "csvpath":csvpath}
                )
                return
            else:
                self._do_run_one_csvpath(QMessageBox.No, path=path, csvpath=csvpath, filename=filename)
        except Exception as e:
            estr = traceback.format_exc()
            self._display_stacktrace(estr)
            meut.warning2(parent=self.main, title="Error", msg=f"Error: {e}")
            return
    """

    @Slot(int)
    def _do_run_one_csvpath(
        self, answer: int, *, csvpath: str, path: CsvPath, filename: str
    ) -> None:
        #
        # if we are a large file and wanted to stop and create a smaller sample
        # return here.
        #
        if answer == QMessageBox.Yes:
            #
            # open file so the user can create a sample
            #
            self.main.selected_file_path = filename
            self.main.read_validate_and_display_file_for_path(
                path=filename, editable=EditStates.EDITABLE
            )
            return
        #
        #
        #
        capture = None
        try:
            path.parse(csvpath)
            path.logger.info(f"starting one-off run: path: {path}, file: {filename}")
            path.update_settings_from_metadata()
            path.ecoms = ErrorCommunications(csvpath=path)
            #
            # setup a printer to capture output
            #
            capture = CapturePrinter()
            #
            # exp. we'll use std out as well as capture so that in debugging/dev we
            # have an incontext output on the console. Doesn't cause problems in prod
            # tho, on mac we have the option to run on the command line, so actually
            # it's potentially helpful there. <<<<< performance degrades, esp. for print,
            # so i'm removing stdout.
            #
            # std = StdOutPrinter()
            # path.set_printers([capture, std])
            path.set_printers([capture])
            #
            # hand off to the test_run worker
            #
            worker = OneOffRunWorker(csvpath=path, csvpath_str=csvpath, printer=capture)

            #
            # what are we updating here
            #
            worker.signals.finished.connect(self._on_test_run_complete)
            worker.signals.messages.connect(self.main.statusBar().showMessage)
            self.main.threadpool.start(worker)

        except Exception as e:
            estr = traceback.format_exc()
            self._display_stacktrace(estr)
            meut.warning2(parent=self.main, title="Error", msg=f"Error: {e}")

    @Slot(tuple)
    def _on_test_run_complete(self, t: tuple) -> None:
        path: CsvPath = t[0]
        csvpath_str: str = t[1]
        lines: list[list[str]] = t[2]
        printer: CapturePrinter = t[3]
        worker = t[4]
        #
        # clear the worker. we have all the generated items now so
        # we don't need to keep it.
        #
        if worker in self.workers:
            self.workers.remove(worker)
        #
        # same as before
        #
        # shut down the logger. not sure this is needed, but ruling stuff out.
        #
        lout.clear_logging(path)
        #
        # display to the user in the lower panel
        #
        self._run_feedback(
            csvpath_str=csvpath_str, path=path, lines=lines, printer=printer
        )
        #
        # there's no absolute need to drop the metadata, but it seems prudent
        #
        self.mdata = None

    """
    def question_warn_file_size_if(self, path) -> bool:
        size = os.path.getsize(path)
        if size <= 1000000:
            return False
        msg = ""
        msg = "Development goes faster with smaller samples. Stop to create a sample?"
        title = "Large file"
        return meut.yesNo(parent=self, msg=msg, title=title)
    """

    def _display_stacktrace(self, trace: str) -> None:
        self._clear_feedback()
        es = QWidget()
        es.setObjectName("Error")
        self.main.helper.help_and_feedback.addTab(es, "Error")
        layout = QVBoxLayout()
        es.setLayout(layout)
        ev = QPlainTextEdit()
        ev.setPlainText(trace)
        ev.setReadOnly(True)
        layout.addWidget(ev)
        layout.setContentsMargins(0, 0, 0, 0)
        self.main.helper.help_and_feedback.setCurrentWidget(es)
        self.main.show_now_or_later(self.main.helper.help_and_feedback)
        if not self.main.helper.is_showing_help():
            self.main.helper.on_click_help()

    def _clear_feedback(self) -> None:
        while self.main.helper.help_and_feedback.count() > 0:
            t = self.main.helper.help_and_feedback.widget(0)
            self.main.helper.help_and_feedback.removeTab(0)
            t.deleteLater()

    def _run_feedback(
        self, *, csvpath_str, path: CsvPath, lines: list, printer: Printer
    ) -> None:
        #
        # remove all tabs (not incl. help)
        #
        self._clear_feedback()
        printouts_label = "Printouts [default]"
        #
        # create new tabs
        #
        #
        # we don't know how many tabs we have (>=1) so do them first iteratively
        #
        for name in printer.names:
            printout = printer.to_string(name)
            default = QWidget()
            printer_name = f"Printouts [{name}]"
            default.setObjectName(printer_name)
            self.main.helper.help_and_feedback.addTab(default, printer_name)

            print_layout = QVBoxLayout()
            default.setLayout(print_layout)
            print_view = QPlainTextEdit()
            #
            # exp! fixed width font fixes the output from the table functions.
            #
            fixed_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
            print_view.setFont(fixed_font)
            #
            #
            #
            printout = printer.to_string(name)

            print_view = RawViewer(
                main=self.main, parent=default, editable=EditStates.UNEDITABLE
            )
            print_view.open_string(printout)

            print_layout.addWidget(print_view)
            print_layout.setContentsMargins(0, 0, 0, 0)

        log = QWidget()
        log.setObjectName("Log")
        self.main.helper.help_and_feedback.addTab(log, "Log")

        errors = QWidget()
        errors.setObjectName("Errors")
        self.main.helper.help_and_feedback.addTab(errors, "Errors")

        matches = QWidget()
        matches.setObjectName("Matches")
        self.main.helper.help_and_feedback.addTab(matches, "Matches")

        variables = QWidget()
        variables.setObjectName("Variables")
        self.main.helper.help_and_feedback.addTab(variables, "Variables")

        code = QWidget()
        code.setObjectName("Code")
        self.main.helper.help_and_feedback.addTab(code, "Automation")

        why = QWidget()
        why.setObjectName("Why")
        self.main.helper.help_and_feedback.addTab(why, "What Am I Seeing?")
        #
        # get the log
        #
        log_lines = lout.get_log_content(self.main.csvpath_config)
        #
        # display data in each tab
        #
        self._display_log(log, log_lines)
        self._display_errors(errors, path.errors)
        self._display_code(code, csvpath_str)
        self._display_matches(matches, lines)
        self._display_variables(variables, path.variables)
        self._display_why(why, path)

        if not self.main.helper.is_showing_help():
            self.main.helper.on_click_help()
        t = self.main.helper.help_and_feedback.findChild(QWidget, printouts_label)
        self.main.helper.help_and_feedback.setCurrentWidget(t)
        self.main.show_now_or_later(self.main.helper.help_and_feedback)

    def _display_log(self, log: QWidget, log_lines: str) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        log.setLayout(layout)
        view = RawViewer(main=self.main, parent=log, editable=EditStates.UNEDITABLE)
        view.open_string(log_lines)
        layout.addWidget(view)

    def _display_matches(self, matches: QWidget, lines: list[list[str]]) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        matches.setLayout(layout)
        model = TableModel(data=lines)
        viewer = DataViewer(
            main=self.main, parent=matches, editable=EditStates.UNEDITABLE
        )
        viewer.display_data(model)
        layout.addWidget(viewer)

    def _display_code(self, code: QWidget, csvpath_str: str) -> None:
        pseudo = f"""
#
# one-off example
#
from csvpath import CsvPath
path = CsvPath(
             '''{csvpath_str}''')
lines = path.collect()
#
# or do:
#
# path.fast-forward()
#
# or
#
# for line in path.next():
#    print(line)
#
#
"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        code.setLayout(layout)
        code_view = RawViewer(
            main=self.main, parent=code, editable=EditStates.UNEDITABLE
        )
        code_view.open_string(pseudo)
        layout.addWidget(code_view)

    def _display_errors(self, errors: QWidget, es: list) -> None:
        es = [e.to_json() for e in es]
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        errors.setLayout(layout)
        errors_view = JsonViewer(
            main=self.main, parent=errors, editable=EditStates.UNEDITABLE
        )
        errors_view.function = "errors"
        sdata = json.dumps(es)
        errors_view.open_file(path=None, data=sdata)
        layout.addWidget(errors_view)

    def _display_variables(self, variables: QWidget, vdata: dict) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        variables.setLayout(layout)
        variables_view = JsonViewer(
            main=self.main, parent=variables, editable=EditStates.UNEDITABLE
        )
        variables_view.function = "variables"
        sdata = json.dumps(vdata)
        variables_view.open_file(path=None, data=sdata)
        layout.addWidget(variables_view)

    def _display_why(self, why: QWidget, path: CsvPath) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        why.setLayout(layout)
        te = QTextEdit()
        layout.addWidget(te)
        runinfo = RunInfo(path)
        t = fiut.make_app_path(f"assets{os.sep}help{os.sep}templates{os.sep}why.html")
        html = HtmlGenerator.load_and_transform(t, runinfo.info)
        te.setText(html)
