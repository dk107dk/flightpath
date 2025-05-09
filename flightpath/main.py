# pylint: disable=C0302
""" The main window and application startup (at bottom, below classes) """
import sys
import os
import csv

from pathlib import Path
from PySide6.QtWidgets import ( # pylint: disable=E0611
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QStackedLayout,
    QInputDialog,
    QProgressDialog,
    QFileDialog,
    QSplitter,
    QTabWidget,
    QSizePolicy,
    QTextEdit
)

from PySide6.QtGui import QIcon # pylint: disable=E0611
from PySide6.QtCore import ( # pylint: disable=E0611
    Qt,
    QFileInfo,
    QThreadPool,
    Slot,
    QItemSelectionModel,
    QModelIndex
)

from csvpath.util.config import Config as CsvPath_Config
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos

from flightpath.workers.csvpath_file_worker import CsvpathFileWorker
from flightpath.workers.general_data_worker import GeneralDataWorker
from flightpath.workers.json_data_worker import JsonDataWorker
from flightpath.widgets.panels.csvpath_viewer import CsvpathViewer
from flightpath.widgets.panels.data_viewer import DataViewer
from flightpath.widgets.panels.json_viewer import JsonViewer
from flightpath.widgets.panels.table_model import TableModel

from flightpath.widgets.sidebars.sidebar import Sidebar
from flightpath.widgets.sidebars.sidebar_named_files import SidebarNamedFiles
from flightpath.widgets.sidebars.sidebar_named_paths import SidebarNamedPaths
from flightpath.widgets.sidebars.sidebar_archive import SidebarArchive
from flightpath.widgets.sidebars.sidebar_functions import SidebarFunctions
from flightpath.widgets.sidebars.sidebar_docs import SidebarDocs

from flightpath.widgets.welcome.welcome import Welcome
from flightpath.widgets.content.content import Content
from flightpath.widgets.config.config import Config

from flightpath.widgets.help.helper import Helper

from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.tabs_utility import TabsUtility as taut
from flightpath.util.state import State


class MainWindow(QMainWindow): # pylint: disable=R0902, R0904
    """ Main GUI component. Does much of the MVC controller lifting. """

    TITLE = "FlightPath Data • Data Preboarding Development"

    def __init__(self):
        super().__init__()
        #
        # please close will be True if the user chooses not to pick a
        # working directory on first startup. This is not expected to
        # happen, but if it did, we need the application initalization
        # code to not put the app into exec.
        #
        self.please_close = False
        self.show()
        self.state = State()
        if not self.state.has_cwd():
            self.state.pick_cwd(self)
            has = self.state.has_cwd()
            if not has:
                self.please_close = True
                return

        self.main = None
        self.main_top = None
        self.main_layout = None
        self.welcome = None
        self.content = None
        self.config = None
        self.table_model = None
        self.sidebar = None
        self.sidebar_rt_top = None
        self.sidebar_rt_mid = None
        self.sidebar_rt_bottom = None
        self.sidebar_functs = None
        self.sidebar_docs = None
        self.rt_tab_box = None
        self.rt_tab_box_layout = None
        self.rt_tab_widget = None
        self.rt_col_helpers = None
        self.rt_col = None
        self._help = None
        self._helper = None
        self.csvpath_config = None
        self.threadpool = None
        self.selected_file_path = None
        self.last_main = None
        self.progress_dialog = None # not sure we need this as a member, but it is used as one atm.
        self.state = State()
        #
        #
        #
        self._load_state_and_cd()

    def _load_state_and_cd(self) -> None:
        """ sets the project directory into .flightpath file, cds to project dir, and reloads UI. """
        self.state.load_state_and_cd(self)
        self.startup()

    def startup(self) -> None:
        """ (re)loads UI """
        self._helper = None
        self.helper
        #
        # state is a json file called ./.state. it is just a ui state
        # persistence tool with some configuration. not sure if it's a
        # keeper by needed today.
        #
        # when we do _load_state we are capturing the path to the state
        # file in the app's starting dir. then, if we find a {cwd:path}
        # key in state we chdir into it.
        #
        self.setWindowTitle(MainWindow.TITLE)
        icon = QIcon(fiut.make_app_path(f"assets{os.sep}icons{os.sep}icon.png"))
        self.setWindowIcon(icon)
        self.threadpool = QThreadPool()

        #
        # this should be Path() not None?
        #
        self.selected_file_path = Path()
        central_widget = self.takeCentralWidget()
        if central_widget:
            central_widget.deleteLater()
        central_widget = QSplitter(self)
        central_widget.setHandleWidth(3)
        central_widget.setStyleSheet("QSplitter::handle { background-color: #f3f3f3;  margin:1px; }")
        self.setCentralWidget(central_widget)

        self._setup_central_widget()
        #
        # tracks the most recent main_layout index so we can return
        # from config or wherever.
        #
        self.last_main = 0
        self.config.config_panel.setup_forms()

        self.show()
        self.statusBar().showMessage(f"  Working directory: {self.state.cwd}")


    def _setup_central_widget(self) -> None:
        """ central widget is a vert splitter with left & right
            sidebars and a main area in the middle of top data
            and bottom help and feedback. """
        cw = self.centralWidget()
        self.main = QSplitter(Qt.Vertical)
        self.main_top = QWidget()
        self.main_layout = QStackedLayout()
        self.main_top.setLayout(self.main_layout)

        self.welcome = Welcome(main=self)
        self.content = Content(main=self)
        self.config = Config(main=self)
        self.main_layout.addWidget(self.welcome)
        self.main_layout.addWidget(self.content)
        self.main_layout.addWidget(self.config)

        self.helper.help_and_feedback_layout = QVBoxLayout()
        self.helper.help_and_feedback.setLayout(self.helper.help_and_feedback_layout)
        self.helper.help_and_feedback_layout.setContentsMargins(0, 0, 0, 0)

        self.main.addWidget(self.main_top)
        self.main.addWidget(self.helper.help_and_feedback)
        self.main.setSizes( [1, 0] )
        self.helper.assure_help_tab()

        self.sidebar = Sidebar(main=self)
        cw.addWidget(self.sidebar)
        cw.addWidget(self.main)
        #
        # exp
        #
        cw.addWidget(self.main)

        #
        # put a tab widget into 3rd column of splitter.
        # 1st tab has the rt_col vert spliter with three file trees
        # 2nd tab has the functions, qualifiers, and maybe docs?
        # hide 2nd tab unless csvpath file is open
        #
        #
        # box for right column of main splitter
        #
        self.rt_tab_box = QWidget()
        self.rt_tab_box_layout = QVBoxLayout()
        self.rt_tab_box.setLayout(self.rt_tab_box_layout)
        self.rt_tab_box_layout.setContentsMargins(1, 3, 4, 3)

        #
        # add right column to splitter
        #
        cw.addWidget(self.rt_tab_box)
        #
        # add tabs within right column box
        #
        self.rt_tab_widget = QTabWidget()
        self.rt_tab_box_layout.addWidget(self.rt_tab_widget)

        #
        # make functions and help splitter
        #
        self.rt_col_helpers = QSplitter(Qt.Vertical)
        #
        # make named-file, named-paths, archive splitter and trees
        #
        self.rt_col = QSplitter(Qt.Vertical)

        self.sidebar_rt_top = SidebarNamedFiles(main=self, config=self.csvpath_config, role=1)
        self.rt_col.addWidget(self.sidebar_rt_top)

        self.sidebar_rt_mid = SidebarNamedPaths(main=self, config=self.csvpath_config, role=2)
        self.rt_col.addWidget(self.sidebar_rt_mid)

        self.sidebar_rt_bottom = SidebarArchive(main=self, config=self.csvpath_config, role=3)
        self.rt_col.addWidget(self.sidebar_rt_bottom)
        #
        # add two tabs to tab widget
        #
        self.rt_tab_widget.addTab(self.rt_col, "Data Management")
        self.rt_tab_widget.addTab(self.rt_col_helpers, "Language Helpers")
        #
        # functions and docs setup below in the tab displaying logic.
        #

        #
        # set size policies. this explicitness may not be strictly necessary.
        #
        self.rt_tab_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.rt_tab_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.rt_tab_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.rt_col_helpers.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.rt_col.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.sidebar_rt_top.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.sidebar_rt_mid.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.sidebar_rt_bottom.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        #
        # hide the tabs if the main_layout is pointed at Welcome or Config
        #
        self.hide_rt_tabs()
        #
        #
        #
        self._connects()

    def renew_sidebar_archive(self) -> None:
        d = self.sidebar_rt_bottom
        self.sidebar_rt_bottom = SidebarArchive(main=self, config=self.csvpath_config, role=3)
        self.rt_col.replaceWidget(2, self.sidebar_rt_bottom)
        self.sidebar_rt_bottom.view.clicked.connect(self.on_archive_tree_click)
        d.deleteLater()

    def renew_sidebar_named_files(self) -> None:
        d = self.sidebar_rt_top
        self.sidebar_rt_top = SidebarNamedFiles(main=self, config=self.csvpath_config, role=3)
        self.rt_col.replaceWidget(0, self.sidebar_rt_top)
        self.sidebar_rt_top.view.clicked.connect(self.on_named_file_tree_click)
        d.deleteLater()

    def renew_sidebar_named_paths(self) -> None:
        d = self.sidebar_rt_mid
        self.sidebar_rt_mid = SidebarNamedPaths(main=self, config=self.csvpath_config, role=3)
        self.rt_col.replaceWidget(1, self.sidebar_rt_mid)
        self.sidebar_rt_mid.view.clicked.connect(self.on_named_paths_tree_click)
        d.deleteLater()

    def hide_rt_tabs(self) -> None:
        i = self.main_layout.currentIndex()
        if i in [0, 2]:
            self.rt_tab_widget.tabBar().hide()

    @property
    def helper(self) -> QTextEdit:
        if self._helper is None:
            self._helper = Helper(self)
        return self._helper

    def _on_data_toolbar_show(self) -> None:
        self.content.toolbar.show()

    def _on_data_toolbar_hide(self) -> None:
        self.content.toolbar.hide()

    def _connects(self) -> None:
        """ some of the connects. may want to consolidate here
            and/or move consolidated to a helper connect class """

        self.rt_tab_widget.currentChanged.connect(self._on_rt_tab_changed)
        self.main_layout.currentChanged.connect(self._on_stack_change)
        self.welcome.clicked.connect(self.welcome.on_click)
        #
        # data_view's sampling toolbar
        #
        self.content.toolbar.sampling.activated.connect(self.on_reload_data)
        self.content.toolbar.rows.activated.connect(self.on_data_rows_changed)
        self.content.toolbar.save_sample.clicked.connect(self.on_save_sample)
        self.content.toolbar.delimiter.activated.connect(self.on_set_delimiter)
        self.content.toolbar.quotechar.activated.connect(self.on_set_quotechar)
        self.content.toolbar.raw_source.clicked.connect(self.on_raw_source)
        #
        #
        #
        self.sidebar.file_navigator.clicked.connect(self.on_tree_click)
        #
        # rt-side trees
        #
        self.sidebar_rt_top.view.clicked.connect(self.on_named_file_tree_click)
        self.sidebar_rt_mid.view.clicked.connect(self.on_named_paths_tree_click)
        self.sidebar_rt_bottom.view.clicked.connect(self.on_archive_tree_click)
        #
        # config stuff
        #
        self.config.toolbar.button_close.clicked.connect(self.close_config)
        self.config.toolbar.button_cancel_changes.clicked.connect(self.cancel_config_changes)
        self.config.toolbar.button_save.clicked.connect(self.save_config_changes)
        #
        #
        #
        self.sidebar.file_navigator.empty_area_click.connect(self.show_welcome_screen)
        self.sidebar.icon_label.clicked.connect(self.show_welcome_screen)

    def setup_named_files(self) -> None:
        """ adds named-files tree """
        self.sidebar_rt_top = SidebarNamedFiles(main=self, config=self.csvpath_config, role=1)
        self.grid_layout.addWidget(self.sidebar_rt_top, 0, 2, 1, 1)

    def setup_named_paths(self) -> None:
        """ adds named-paths tree """
        self.sidebar_rt_mid = SidebarNamedPaths(main=self, config=self.csvpath_config, role=2)
        self.grid_layout.addWidget(self.sidebar_rt_mid, 1, 2, 1, 1)

    def setup_archive(self) -> None:
        """ adds archive tree """
        self.sidebar_rt_bottom = SidebarArchive(main=self, config=self.csvpath_config, role=3)
        self.grid_layout.addWidget(self.sidebar_rt_bottom, 2, 2, 1, 1)

    @Slot()
    def show_welcome_screen(self):
        """ shows the main area welcome image + buttons """
        self.sidebar.file_navigator.selectionModel().clear()
        self._show_welcome_but_do_not_deselect()

    def _show_welcome_but_do_not_deselect(self) -> None:
        self.last_main = self.main_layout.currentIndex()
        self.main_layout.setCurrentIndex(0)
        self.statusBar().showMessage(self.state.cwd)

    def _on_rt_tab_changed(self) -> None:
        ...

    def _rt_tabs_hide(self) -> None:
        self.rt_tab_widget.tabBar().setCurrentIndex(0)
        self.rt_tab_widget.tabBar().hide()

    def _rt_tabs_show(self) -> None:
        self.rt_tab_widget.tabBar().show()

    def _on_stack_change(self) ->None:
        i = self.main_layout.currentIndex()
        if i in [0, 2]:
            self._rt_tabs_hide()
        else:
            #
            # we're switching to data or a csvpath file. that means we show the helper tab
            # and make both visible in the tabbar. if we haven't shown the tabbar before we
            # don't have a populated helper tree, so we need to get on that.
            #
            self._rt_tabs_show()
            if self.rt_col_helpers.count() == 0:
                self.sidebar_functs = SidebarFunctions(main=self)
                self.rt_col_helpers.addWidget(self.sidebar_functs)
                self.sidebar_docs = SidebarDocs(main=self, functions=self.sidebar_functs.functions)
                self.rt_col_helpers.addWidget(self.sidebar_docs)

    @Slot(tuple)
    def update_json_views(self, worker_data):
        filepath, data, editable = worker_data   # pylint: disable=W0612
        self.progress_dialog.close()
        self.last_main = self.main_layout.currentIndex()
        #
        # show code/data tabs' panel
        #
        self.main_layout.setCurrentIndex(1)
        #
        # hide grid, source tabs
        #
        json_view = taut.find_tab(self.content.tab_widget, filepath)
        if json_view is None:
            json_view = JsonViewer(self, editable)
            json_view.open_file(path=filepath, data=data)
            json_view.setObjectName(filepath)
            self.content.tab_widget.addTab(json_view, os.path.basename(filepath) )
        else:
            json_view = json_view[1]
        taut.select_tab(self.content.tab_widget, json_view)
        self._rt_tabs_hide()

    @Slot(tuple)
    def update_csvpath_views(self, worker_data):
        filepath, data, editable = worker_data # pylint: disable=W0612
        self.progress_dialog.close()
        self.last_main = self.main_layout.currentIndex()
        #
        # show code/data tabs' panel
        #
        self.main_layout.setCurrentIndex(1)
        #
        # hide grid, source tabs
        # when csvpath source_view is visible we hide the sample tool bar
        #
        self.content.toolbar.disable()
        #
        #
        #
        csvpath_view = taut.find_tab(self.content.tab_widget, filepath)
        if csvpath_view is None:
            editable = editable if editable is not None else True
            csvpath_view = CsvpathViewer(main=self, editable=editable)
            csvpath_view.setObjectName(filepath)
            csvpath_view.open_file(path=filepath, data=data)
            self.content.tab_widget.addTab(csvpath_view, os.path.basename(filepath) )
        else:
            csvpath_view = csvpath_view[1]
        csvpath_view.editable = editable if editable else True
        taut.select_tab(self.content.tab_widget, csvpath_view)
        #
        # we show the right tabs in order to show the functions and docs
        #
        self._rt_tabs_show()

    @Slot(tuple)
    def update_views(self, worker_data):
        msg, lines, filepath, data, lines_to_take = worker_data # pylint: disable=W0612
        self.table_model = TableModel(data)
        #
        # we're going to put a button on the toolbar to switch to a raw source
        # display, rather than have another tab for the same doc. for now, just
        # disable
        #
        # self.content.source_view.open_file(filepath, lines)
        #
        self.progress_dialog.close()
        self.last_main = self.main_layout.currentIndex()
        self.main_layout.setCurrentIndex(1)
        #
        # need to add a tab
        #   need to check if a tab already exists?
        #
        obj_name = filepath
        data_view = taut.find_tab(self.content.tab_widget, filepath)
        if data_view is None:
            data_view = DataViewer(parent=self.content)
            data_view.setObjectName(obj_name)
            #
            # make sure we have the lines so the raw_viewer can take the same
            #
            data_view.lines_to_take = lines_to_take
            name = os.path.basename(filepath)
            self.content.tab_widget.addTab(data_view, name)
        else:
            #
            # find_tab -> (index, widget)
            #
            data_view = data_view[1]
        data_view.display_data(self.table_model)
        #
        # when  data _view is visible we show the sample tool bar
        #
        self.content.toolbar.enable()
        self.content.toolbar.show()
        #
        # hide right tabs because we don't need csvpath helpers when looking
        # at data
        #
        #self._rt_tabs_hide()
        taut.select_tab(self.content.tab_widget, data_view)


    def on_data_rows_changed(self) -> None:
        t = self.content.toolbar.rows.currentText()
        if t == "All lines":
            #
            # set the sampling options to first-n and remove or disable others
            #
            self.content.toolbar.sampling.setCurrentIndex(0)
            self.content.toolbar.sampling.model().item(0).setEnabled(False)
            self.content.toolbar.sampling.model().item(1).setEnabled(False)
            self.content.toolbar.sampling.model().item(2).setEnabled(False)
            #
            # select first-n
            #
        else:
            self.content.toolbar.sampling.model().item(0).setEnabled(True)
            self.content.toolbar.sampling.model().item(1).setEnabled(True)
            self.content.toolbar.sampling.model().item(2).setEnabled(True)
            #
            # add/enable all sampling options
            #
        #
        # tell data to reload. the worker will known what to do about
        # sampling and number of lines
        #
        self.read_validate_and_display_file()

    def read_validate_and_display_file(self, editable=True):
        info = QFileInfo(self.selected_file_path)
        #
        # TODO: consolidate below
        #
        # pylint thinks csv_file_extensions doesn't support membership tests but it is list[str]. :/
        if info.isFile() and info.suffix() in self.csvpath_config.csv_file_extensions: # pylint: disable=E1135
            worker = GeneralDataWorker(
                self.selected_file_path,
                self,
                rows=self.content.toolbar.rows.currentText(),
                sampling=self.content.toolbar.sampling.currentText(),
                delimiter=self.content.toolbar.delimiter_char(),
                quotechar=self.content.toolbar.quotechar_char()
            )
            worker.signals.finished.connect(self.update_views)
            worker.signals.messages.connect(self.statusBar().showMessage)
            self.progress_dialog = QProgressDialog("Loading...", None, 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setValue(0)
            self.progress_dialog.setMinimumDuration(400)
            self.threadpool.start(worker)
        # pylint thinks csvpath_file_extensions doesn't support membership tests but it is list[str]. :/
        elif info.isFile() and info.suffix() in self.csvpath_config.csvpath_file_extensions: # pylint: disable=E1135
            worker = CsvpathFileWorker(self.selected_file_path, self, editable=editable)
            worker.signals.finished.connect(self.update_csvpath_views)
            worker.signals.messages.connect(self.statusBar().showMessage)
            self.progress_dialog = QProgressDialog("Loading...", None, 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setValue(0)
            self.progress_dialog.setMinimumDuration(400)
            self.threadpool.start(worker)
        elif info.isFile() and info.suffix() == "json":
            worker = JsonDataWorker(self.selected_file_path, self, editable=editable)
            worker.signals.finished.connect(self.update_json_views)
            worker.signals.messages.connect(self.statusBar().showMessage)
            self.progress_dialog = QProgressDialog("Loading...", None, 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setValue(0)
            self.progress_dialog.setMinimumDuration(400)
            self.threadpool.start(worker)
        #
        # need to recognize .txt (if not in csv extensions) and .md
        #
        else:
            self.clear_views()



    @Slot(QModelIndex)
    def on_tree_click(self, index):
        if not index.isValid():
            return
        source_index = self.sidebar.proxy_model.mapToSource(index)
        if not source_index.isValid():
            return
        file_info = self.sidebar.file_model.fileInfo(source_index)
        self.selected_file_path = file_info.filePath()
        nos = Nos(self.selected_file_path)
        if not nos.isfile():
            return
        info = QFileInfo(self.selected_file_path)
        editable = info.suffix() in self.csvpath_config.csvpath_file_extensions
        editable = editable or info.suffix() in ["json", "md", "txt"]
        self.read_validate_and_display_file(editable=editable)
        self.statusBar().showMessage(f"  {self.selected_file_path}")
        #
        # store the index for use in the case the user clicks off the current file
        # but then responds no to a confirm box.
        #
        self.sidebar.last_file_index = index

    def on_named_file_tree_click(self, index):
        self.selected_file_path = self.sidebar_rt_top.model.filePath(index)
        nos = Nos(self.selected_file_path)
        if not nos.isfile():
            ...
            #self._show_welcome_but_do_not_deselect()
        else:
            self.read_validate_and_display_file(editable=False)
            self.statusBar().showMessage(f"  {self.selected_file_path}")

    def on_named_paths_tree_click(self, index):
        self.selected_file_path = self.sidebar_rt_mid.model.filePath(index)
        nos = Nos(self.selected_file_path)
        if not nos.isfile():
            ...
            #self._show_welcome_but_do_not_deselect()
        else:
            self.read_validate_and_display_file(editable=False)
            self.statusBar().showMessage(f"  {self.selected_file_path}")

    def on_archive_tree_click(self, index):
        self.selected_file_path = self.sidebar_rt_bottom.model.filePath(index)
        nos = Nos(self.selected_file_path)
        if not nos.isfile():
            ...
            #self._show_welcome_but_do_not_deselect()
        else:
            self.read_validate_and_display_file(editable=False)
            self.statusBar().showMessage(f"  {self.selected_file_path}")

    def clear_views(self):
        self.content.close_all_tabs()

    def on_help_click(self) -> None:
        ss = self.main.sizes()
        if ss[1] > 0:
            self.main.setSizes([1, 0])
        else:
            self.main.setSizes([4, 1])

    def on_set_cwd_click(self):
        path = QFileDialog.getExistingDirectory(self)
        if path:
            path = str(path)
            self.state.cwd = path
            self._load_state_and_cd()
            self.statusBar().showMessage(f"  Working directory changed to: {self.state.cwd}")

    def on_reload_data(self) -> None:
        self.read_validate_and_display_file()

    def on_set_delimiter(self) -> None:
        self.read_validate_and_display_file()

    def on_set_quotechar(self) -> None:
        self.read_validate_and_display_file()

    def on_raw_source(self) -> None:
        #self.content.raw_viewer.open_file(filepath)
        #self.last_main = self.main_layout.currentIndex()
        #self.main_layout.setCurrentIndex(1)
        #
        # no need to add a tab. we already have one because the grid is default.
        #
        obj_name = self.selected_file_path
        data_view = taut.find_tab(self.content.tab_widget, obj_name)
        data_view[1].toggle_grid_raw()


    def on_save_sample(self) -> None:
        if not self.table_model:
            raise ValueError("Table model cannot be None")
        name = os.path.basename(self.selected_file_path)
        path = os.path.dirname(self.selected_file_path)
        #
        # minimal change to help us not overwrite
        #
        new_name, ok = QInputDialog.getText(self, "Save sample", "Enter a name for the sample file:", text=name)
        if ok and new_name:
            path = fiut.deconflicted_path(path, new_name)
            data = self.table_model.get_data()
            with DataFileWriter(path=path) as file: # pylint: disable=E0110
                writer = csv.writer(file.sink)
                writer.writerows(data)
        #
        # reload views with new file
        # set the file tree to highlight the new file
        #
        self.read_validate_and_display_file()
        #
        # i have a path str
        # i need the proxy model index at that path
        #   1. get file_model index at path
        #   2. get proxy model index mapped to source model index
        # give proxy model index to tree_view to select
        #
        index = self.sidebar.file_model.index(path)
        pindex = self.sidebar.proxy_model.mapFromSource(index)
        if index.isValid():
            self.sidebar.file_navigator.setCurrentIndex(pindex)

    def open_config(self):
        self.last_main = self.main_layout.currentIndex()
        self.main_layout.setCurrentIndex(2)
        self.config.show_help()

    #
    # this needs to go back to whatever doc is selected, if one was. for now we
    # can just go back to welcome.
    #
    def close_config(self):
        i = self.main_layout.currentIndex()
        self.main_layout.setCurrentIndex(self.last_main)
        self.last_main = i
        self.config.close_help()

    def cancel_config_changes(self):
        self.config.config_panel.populate_all_forms()
        self.config.toolbar.button_close.setEnabled(True)
        self.config.toolbar.button_cancel_changes.setEnabled(False)
        self.config.toolbar.button_save.setEnabled(False)

    def save_config_changes(self):
        self.config.config_panel.save_all_forms()
        self.config.toolbar.button_close.setEnabled(True)
        self.config.toolbar.button_cancel_changes.setEnabled(False)
        self.config.toolbar.button_save.setEnabled(False)

    def on_config_changed(self):
        if hasattr(self, "config") and self.config:
            self.config.toolbar.button_close.setEnabled(False)
            self.config.toolbar.button_cancel_changes.setEnabled(True)
            self.config.toolbar.button_save.setEnabled(True)

    def closeEvent(self, event):
        if (
            not hasattr(self, "sidebar")
            and not hasattr(self, "main_layout")
            and not hasattr(self, "content")
        ):
            event.accept()
            return
        elif (
            self.sidebar.last_file_index or
            not self.content.all_files_are_saved()
        ):
            if not self.content.close_all_tabs():
                event.ignore()

def run():
    app = QApplication(sys.argv)
    app.setApplicationName(MainWindow.TITLE)
    app.setStyle("Fusion")

    window = MainWindow()
    if window.please_close:
        return
    #
    # careful, this was throwing an error at one point, but is currently
    # commented mainly because a smaller window is easier for dev.
    #
    #window.showMaximized()
    #window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run()
