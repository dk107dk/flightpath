import os
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
from csvpath.util.nos import Nos

from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.widgets.icon_packager import IconPackager
from flightpath.widgets.panels.table_model import TableModel
from flightpath.dialogs.find_file_name_one_context_menu import NameOneLineEdit

from flightpath.util.help_finder import HelpFinder
from flightpath.util.log_utility import LogUtility as lout
from flightpath.util.tabs_utility import TabsUtility as tabu

class FindFileByReferenceDialog(QDialog):

    def __init__(self, *, main):
        super().__init__(main)
        self.main = main
        self.paths = CsvPaths()

        self.setWindowTitle("Find files by reference")

        self.resize(700, 290)
        self.setSizeGripEnabled(True)
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

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
        # exp
        #
        #self.name_one.setContextMenuPolicy(Qt.CustomContextMenu)
        #self.name_one.customContextMenuRequested.connect(self._show_name_one_context_menu)

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
        #
        #
        #self.table_view = QTableView()
        #main_layout.addWidget(self.table_view)
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
        #self.howto.show()
        self.stack_layout.setCurrentIndex(1)
        main_layout.addWidget(self.stacker)
        #
        # end exp
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
        #self._setup_view_context_menu()
        self.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, position) -> None:
        index = self.table_view.indexAt(position)
        if index.isValid():
            global_pos = self.table_view.viewport().mapToGlobal(position)
            row = index.row()
            context_menu = QMenu(self)
            open_file_action = QAction()
            open_file_action.setText("Open file")
            open_file_action.triggered.connect(lambda: self._open_file(row))
            show_metadata_action = QAction()
            show_metadata_action.setText("Show metadata")
            show_metadata_action.triggered.connect(lambda: self._show_metadata(row))
            context_menu.addAction(open_file_action)
            context_menu.addAction(show_metadata_action)
            context_menu.exec(global_pos)

    def _show_metadata(self, row) -> None:
        item_index = self.model.index(row, 0)
        item = self.model.itemFromIndex(item_index)
        t = item.text()
        datatype = self.datatype.currentText()
        if datatype == "files":
            self._show_named_file_metadata(t)

    def _show_named_file_metadata(self, path) -> None:
        self.selected_file_path = path
        files_root = self.main.csvpath_config.get(section="inputs", name="files")
        if not path.startswith(files_root):
            #
            # this shouldn't happen, but what if it did?
            #
            raise ValueError("The selected file path does not match the named-files root path")
        sep = pathu.sep(files_root)
        self.named_file_name = path[len(files_root)+1:]
        self.named_file_name = self.named_file_name[0:self.named_file_name.find(sep[0])]
        self.mpath = self.paths.file_manager.named_file_home(self.named_file_name)
        self.mpath = os.path.join(self.mpath, "manifest.json")
        nos = Nos(self.mpath)
        if not nos.exists():
            #
            # this should never happen, unless files have been rotated, maybe?
            #
            raise ValueError(f"The named-file manifest is not found at {mpath}")
        #
        # can we open as editable, but not provide a save? that would give us the ability to
        # click into values and copy them.
        #
        worker = self.main.read_validate_and_display_file_for_path(self.mpath, editable=True)
        worker.signals.finished.connect(self.on_load_find_in_file)


    def on_load_find_in_file(self) -> None:
        path = self.selected_file_path
        #
        # we're open. but we have no idea which doc we need.
        #
        mani = self.paths.file_manager.get_manifest(self.named_file_name)
        fingerprint = os.path.basename(path)
        fingerprint = fingerprint[0:fingerprint.rfind(".")]
        i = 0
        for i, entry in enumerate(mani):
            if entry["fingerprint"] == fingerprint:
                break
        #
        # find the tab showing the mani
        #
        w = tabu.find_tab(self.main.content.tab_widget, self.mpath)
        if w is None:
            raise RuntimeError("Unable to find manifest.json view")
        #
        # open the node that represents the entry
        #
        index = w[1].view.model().index(i, 0)
        w[1].view.setCurrentIndex(index)
        w[1].view.setExpanded(index, True)


    def _open_file(self, row) -> None:
        item_index = self.model.index(row, 0)
        item = self.model.itemFromIndex(item_index)
        t = item.text()
        datatype = self.datatype.currentText()
        if datatype == "files":
            self._open_named_file(t)


    def _open_named_file(self, path) -> None:
        #
        # we don't want the main manifest because 1) it doesn't 100% always
        # get created -- it is considered the "default" integration, so it can
        # be turned off. and 2) it will grow fast and may be rotated more
        # frequently.
        #
        #fileinputs = self.paths.file_manager.files_root_manifest_path
        #mani = self.paths.file_manager.files_root_manifest
        #
        files_root = self.main.csvpath_config.get(section="inputs", name="files")
        if not path.startswith(files_root):
            #
            # this shouldn't happen, but what if it did?
            #
            raise ValueError("The selected file path does not match the named-files root path")
        #sep = pathu.sep(files_root)
        #named_file_name = path[len(files_root):]
        #named_file_name = named_file_name[0:named_file_name.find(sep)]
        #mani = self.paths.file_manager.get_manifest(named_file_name)
        self.main.read_validate_and_display_file_for_path(path, editable=False)
        #
        # open fileinputs in JSON view
        #
        # open the node representing the named-file staging that created path
        #

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
            #self.named_x_name.show()
            self.main.show_now_or_later(self.name_one)
            #self.name_one.show()
            self.main.show_now_or_later(self.box)
            #self.box.show()
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
            #self.howto.show()
            self.stack_layout.setCurrentIndex(1)
        elif datatype == "results":
            md = HelpFinder(main=self.main).help("find_data/results_queries.md")
            self.howto.setMarkdown(md)
            self.main.show_now_or_later(self.howto)
            #self.howto.show()
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
        name = self.named_x_name.currentText()
        datatype = self.datatype.currentText()
        if name == "..." or datatype == "...":
            return False
        return True

    def _on_pick_name(self) -> None:
        name = self.named_x_name.currentText()
        datatype = self.datatype.currentText()
        if not self._can_make_reference():
            self.stack_layout.setCurrentIndex(1)
            self.model.clear()
            self.results_description.setText("")
            return
        try:
            if self.last_name != name:
                self.name_one.setText(":all")
            r = self._make_reference()
            q = self._resolve(r, datatype)
            self.ref = q.ref
            res = q.files
            if isinstance(res, str):
                res = [res]
            number = len(res) if res else 0
            if res:
                self.add_data(res)
            else:
                self.model.clear()
            if res:
                t = self._generate_hints(q.ref.next)
                self.hints_text.setText(t)
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
            text = "Start with a path, a date, a range like :yesterday, :after, or :all, or an ordinal like :first or an index like :5"
        elif not tokens or len(tokens) == 0:
            return "This reference cannot be extended"
        else:
            tokens = [self._token_to_hint(t) for t in tokens]
            text = f"You can add: {' or '.join(tokens)}"
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


