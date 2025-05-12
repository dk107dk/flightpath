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
        QApplication
)

from PySide6.QtGui import QClipboard, QStandardItemModel, QStandardItem, QAction
from PySide6.QtCore import Qt # pylint: disable=E0611

from csvpath import CsvPaths
from csvpath.util.references.files_reference_finder import FilesReferenceFinder
from csvpath.util.references.results_reference_finder import ResultsReferenceFinder
from csvpath.util.path_util import PathUtility as pathu
from csvpath.util.nos import Nos

from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.widgets.icon_packager import IconPackager
from flightpath.widgets.panels.table_model import TableModel

from flightpath.util.help_finder import HelpFinder
from flightpath.util.log_utility import LogUtility as lout
from flightpath.util.tabs_utility import TabsUtility as tabu

class FindFileByReferenceDialog(QDialog):

    def __init__(self, *, main):
        super().__init__(main)
        self.main = main
        self.paths = CsvPaths()

        self.setWindowTitle("Find files by reference")

        self.setFixedHeight(290)
        self.setFixedWidth(700)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        #self.setWindowModality(Qt.ApplicationModal)

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

        self.datatype = QComboBox()
        ref_line_layout.addWidget(self.datatype)
        self.datatype.addItem("...")
        self.datatype.addItem("files")
        self.datatype.addItem("results")
        self.datatype.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.datatype.activated.connect(self._on_pick_datatype)

        self.path = QLineEdit()
        paths = [f"assets{os.sep}icons{os.sep}copy.svg", HelpIconPackager.HELP_ICON]
        on_click = [self._on_copy, self._on_help]

        box = IconPackager.add_svg_icon(main=main, widget=self.path, on_click=on_click, icon_path=paths )
        self.path.textChanged.connect(self._on_pick_name)
        ref_line_layout.addWidget(box)


        self.table_view = QTableView()
        main_layout.addWidget(self.table_view)
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
        if datatype == "files":
            self._add_named_files()
        else:
            self._add_named_results()
        self._on_pick_name()

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

    def _on_help(self) -> None:
        ...

    def _resolve( self, r:str, datatype:str) -> str|list[str]:
        if datatype == "files":
            try:
                finder = FilesReferenceFinder(self.paths, name=r)
                return finder.resolve()
            except Exception as e:
                print(f"Error: {type(e)}: {e}")
                return None
        else:
            try:
                finder = ResultsReferenceFinder(self.paths, name=r)
                return finder.resolve(with_instance=False)
            except Exception as e:
                print(f"Error: {type(e)}: {e}")
                return None

    def _make_reference(self) -> str:
        name = self.named_x_name.currentText()
        datatype = self.datatype.currentText()
        path = self.path.text()
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
            self.model.clear()
            self.results_description.setText("")
            return
        r = self._make_reference()
        res = self._resolve(r, datatype)
        if isinstance(res, str):
            res = [res]
        number = len(res) if res else 0
        if res:
            self.add_data(res)
        else:
            self.model.clear()
        self.results_description.setText(f"  {number} named-{datatype} found with reference {r}")

