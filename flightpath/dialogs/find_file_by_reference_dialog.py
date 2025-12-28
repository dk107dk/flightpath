import os
import json
from PySide6.QtWidgets import ( # pylint: disable=E0611
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QDialog,
        QLineEdit,
        QComboBox,
        QMenu,
        QScrollArea,
        QWidget,
        QPlainTextEdit,
        QTableView,
        QHeaderView,
        QSizePolicy,
        QApplication,
        QStackedLayout,
        QTextEdit

)

from PySide6.QtGui import QClipboard, QStandardItemModel, QStandardItem, QAction
from PySide6.QtCore import Qt # pylint: disable=E0611

from csvpath import CsvPaths
from csvpath.util.references.files_reference_finder_2 import FilesReferenceFinder2 as FilesReferenceFinder
from csvpath.util.references.results_reference_finder_2 import ResultsReferenceFinder2 as ResultsReferenceFinder
from csvpath.util.path_util import PathUtility as pathu
from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos

from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.widgets.icon_packager import IconPackager
from flightpath.dialogs.find_file_name_one_context_menu import NameOneLineEdit
from flightpath.dialogs.reference_files.reference_file_handler import ReferenceFileHandler
from flightpath.util.help_finder import HelpFinder
from flightpath.util.log_utility import LogUtility as lout
from flightpath.util.tabs_utility import TabsUtility as tabu

from flightpath.editable import EditStates

class FindFileByReferenceDialog(QDialog):

    def __init__(self, *, main):
        super().__init__(None)
        self.main = main
        self.paths = CsvPaths()

        self.setWindowTitle("Find files by reference")

        self.resize(700, 290)
        self.setSizeGripEnabled(True)
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.NonModal)
        #
        # named file name
        #
        ref_line = QWidget()
        ref_line_layout = QHBoxLayout()
        ref_line.setLayout(ref_line_layout)
        main_layout.addWidget(ref_line)

        self.named_x_name = QComboBox()
        ref_line_layout.addWidget(self.named_x_name)
        self.named_x_name.addItem("...")
        self.named_x_name.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.named_x_name.activated.connect(self._on_pick_name)
        self.named_x_name.hide()
        #
        # this is always the last name, but the last name does not always make a good reference
        #
        self.last_name = None
        #
        # this is the last reference. it has the hints but not the query.
        #
        self.ref = None
        self.datatype = QComboBox()
        ref_line_layout.addWidget(self.datatype)
        self.datatype.addItem("...")
        self.datatype.addItem("files")
        self.datatype.addItem("results")
        self.datatype.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.datatype.activated.connect(self._on_pick_datatype)
        #
        # this is ReferenceParser.name_one and ReferenceParser.name_one_tokens
        #
        self.name_one = NameOneLineEdit(parent=self)
        self.name_one.textChanged.connect(self._on_pick_name)
        #
        #
        #
        ref_line_layout.addWidget(self.name_one)
        self.name_one.hide()
        paths = [f"assets{os.sep}icons{os.sep}copy.svg", HelpIconPackager.HELP_ICON]
        on_click = [self._on_copy, self._on_help_find_files]
        self.box = IconPackager.add_svg_icon(main=main, widget=self.name_one, on_click=on_click, icon_path=paths )
        ref_line_layout.addWidget(self.box)
        self.box.hide()
        #
        #
        #
        self.hints = QScrollArea()
        self.hints.setWidgetResizable(True)
        self.hints.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.hints.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.hints.setFixedHeight(35)
        self.hints_text = QLabel()
        self.hints_text.setText("")
        self.hints.setWidget(self.hints_text)
        main_layout.addWidget(self.hints)
        #
        #
        #
        self.stacker = QWidget()
        self.stack_layout = QStackedLayout()
        self.stacker.setLayout(self.stack_layout)
        self.table_view = QTableView()
        self.stack_layout.addWidget(self.table_view)

        self.howto = QTextEdit()
        self.howto.setReadOnly(True)
        self.howto.setObjectName("How-to")
        self.stack_layout.addWidget(self.howto)
        md = HelpFinder(main=self.main).help("find_data/howto.md")
        self.howto.setMarkdown(md)

        self.main.show_now_or_later(self.howto)
        self.stack_layout.setCurrentIndex(1)
        main_layout.addWidget(self.stacker)
        #
        #
        #
        self.model = QStandardItemModel(self)
        self.model.setColumnCount(1)
        self.table_view.setModel(self.model)
        header = self.table_view.horizontalHeader()
        header.hide()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_view.verticalHeader().setVisible(False)

        self.count = QScrollArea()
        self.count.setWidgetResizable(True)
        self.count.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.count.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.count.setFixedHeight(35)

        self.results_description = QLabel()
        self.results_description.setText("")
        self.count.setWidget(self.results_description)

        main_layout.addWidget(self.count)

        self.context_menu = None
        self.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self._show_context_menu)
        #
        # mpath holds the path to the last manifest loaded
        #
        self.mpath = None


    def _show_context_menu(self, position) -> None:
        index = self.table_view.indexAt(position)
        if index.isValid():
            global_pos = self.table_view.viewport().mapToGlobal(position)
            row = index.row()
            context_menu = QMenu(self)
            open_file_action = QAction()
            show_run_action = None
            #
            # if we're looking at named-results and specify data.csv or unmatched.csv
            # we'll open one of those. otherwise, if we're looking at a named-file's
            # data files we'll open the bytes. And if we're looking at named-results,
            # the run_dir or an instance, we'll open the named-file that was the source
            # data. TBD if we'll deal with any source-mode preceding. probably not.
            #
            self.reference_file_handler = ReferenceFileHandler(parent=self)
            if self.datatype.currentText() == "results":
                if(
                    self.name_one.text().endswith(":data")
                    or self.name_one.text().endswith(":unmatched")
                ):
                    open_file_action.triggered.connect(lambda: self.reference_file_handler._open_results_file(row))
                    open_file_action.setText("Open results data file")
                else:
                    #
                    # WARN: rt-click on RESULT but showing named-file. could confuse the display code.
                    #
                    open_file_action.triggered.connect(lambda: self.reference_file_handler._open_origin_file(row))
                    open_file_action.setText("Open source data file")

                    show_run_action = QAction()
                    show_run_action.triggered.connect(lambda: self.reference_file_handler._show_run_dir(row))
                    show_run_action.setText("Show run")
            else:
                open_file_action.setText("Open data file")
                open_file_action.triggered.connect(lambda: self.reference_file_handler._open_files_file(row))

            show_metadata_action = QAction()
            show_metadata_action.setText("Show metadata")
            show_metadata_action.triggered.connect(lambda: self.reference_file_handler._show_manifest(row))
            #
            #
            #
            copy_path_action = QAction()
            copy_path_action.setText("Copy path")
            copy_path_action.triggered.connect(lambda: self.reference_file_handler._copy_path(row))

            #
            #
            #
            if show_run_action is not None:
                context_menu.addAction(show_run_action)
            context_menu.addAction(open_file_action)
            context_menu.addAction(show_metadata_action)
            context_menu.addAction(copy_path_action)
            context_menu.exec(global_pos)


    def add_data(self, data_list:list[str]) -> None:
        self.model.clear()
        for text in data_list:
            item = QStandardItem(text)
            self.model.appendRow(item)

    def _on_pick_datatype(self) -> None:
        datatype = self.datatype.currentText()
        if datatype in ["files", "results"]:
            if datatype == "files":
                self._add_named_files()
            elif datatype == "results":
                self._add_named_results()
            self._on_pick_name()
            self.main.show_now_or_later(self.named_x_name)
            self.main.show_now_or_later(self.name_one)
            self.main.show_now_or_later(self.box)
        else:
            self.named_x_name.hide()
            self.name_one.hide()
            self.box.hide()
        #
        # zero out other controls
        #

        #
        # show the query help for the datatype
        #
        if datatype == "files":
            md = HelpFinder(main=self.main).help("find_data/file_queries.md")
            self.howto.setMarkdown(md)
            self.main.show_now_or_later(self.howto)
            self.stack_layout.setCurrentIndex(1)
        elif datatype == "results":
            md = HelpFinder(main=self.main).help("find_data/results_queries.md")
            self.howto.setMarkdown(md)
            self.main.show_now_or_later(self.howto)
            self.stack_layout.setCurrentIndex(1)
        else:
            ...


    def _add_named_files(self) -> None:
        mgr = self.paths.file_manager
        named_files = mgr.named_file_names
        self.named_x_name.clear()
        self.named_x_name.addItem("...")
        for name in named_files:
            self.named_x_name.addItem(name)
        self._on_pick_name()

    def _add_named_results(self) -> None:
        mgr = self.paths.results_manager
        named_results = mgr.list_named_results()
        self.named_x_name.clear()
        self.named_x_name.addItem("...")
        for name in named_results:
            self.named_x_name.addItem(name)

    def show_dialog(self) -> None:
        self.exec()

    def _on_copy(self) -> None:
        if not self._can_make_reference():
            print("cannot make reference")
            return
        r = self._make_reference()
        clipboard = QApplication.instance().clipboard()
        clipboard.setText(self._make_reference())

    def _on_help_find_files(self) -> None:
        md = HelpFinder(main=self.main).help("find_file_by_reference_dialog/help.md")
        if md is None:
            self.main.helper.close_help()
            return
        self.main.helper.get_help_tab().setMarkdown(md)
        if not self.main.helper.is_showing_help():
            self.main.helper.on_click_help()

    def _resolve( self, r:str, datatype:str) -> str|list[str]:
        finder = None
        if datatype == "files":
            finder = FilesReferenceFinder(self.paths, reference=r)
        else:
            finder = ResultsReferenceFinder(self.paths, reference=r)
        return finder.query()

    def _make_reference(self) -> str:
        name = self.named_x_name.currentText()
        datatype = self.datatype.currentText()
        path = self.name_one.text()
        r = f"${name}.{datatype}.{path}"
        return r

    def _can_make_reference(self) -> bool:
        #
        # returns true if we have a major name and a datatype, allowing
        # us to build a reference by filling in name_one, etc.
        #
        name = self.named_x_name.currentText()
        datatype = self.datatype.currentText()
        if name == "..." or datatype == "...":
            return False
        return True

    def _on_pick_name(self) -> None:
        #
        # name is the root major
        #
        name = self.named_x_name.currentText()
        datatype = self.datatype.currentText()
        if not self._can_make_reference():
            #
            # we're missing either a major or a datatype
            #
            self.stack_layout.setCurrentIndex(1)
            self.model.clear()
            self.results_description.setText("")
            return
        try:
            #
            # if we changed root major we zero out the results and
            # set :all, the default, as name_one
            #
            if self.last_name != name:
                self.name_one.setText(":all")
            r = self._make_reference()
            q = self._resolve(r, datatype)
            self.ref = q.ref
            res = q.files
            if res:
                self.add_data(res)
                n = q.ref.next
                t = self._generate_hints(n)
                self.hints_text.setText(t)
            else:
                self.model.clear()
            number = len(res) if res else 0
            self.results_description.setText(f"  {number} named-{datatype} found with reference {r}")
            self.stack_layout.setCurrentIndex(0)
        except Exception as e:
            self.model.clear()
            if self.name_one.text() is None or self.name_one.text().strip() == "":
                t = self._generate_hints([])
                self.hints_text.setText(t)
            print(f"Error: {type(e)}: {e}")
        self.last_name = name


    def _generate_hints(self, tokens:list[str]) -> str:
        text = ""
        t = self.name_one.text()
        if t is None or t.strip() == "":
            text = "  Start with a path, a date, a range like :yesterday, :after, or :all, or an ordinal like :first or an index like :5"
        elif not tokens or len(tokens) == 0:
            return "  This reference cannot be extended"
        else:
            tokens = [self._token_to_hint(t) for t in tokens]
            text = f"  You can add: {' or '.join(tokens)}"
        return text

    def _token_to_hint(self, t:str) -> str:
        t = t[t.rfind("_")+1:]

        if t == "arrival":
            t = "an arrival time"
        elif t == "ordinal":
            t = "an ordinal like :first, :last, or an index like :5"
        elif t == "range":
            t = "a range like :before or :from"
        return t


