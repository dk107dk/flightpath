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
    QMessageBox,
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

from flightpath.workers.csvpath_file_worker import CsvpathFileWorker
from flightpath.workers.general_data_worker import GeneralDataWorker
from flightpath.workers.json_data_worker import JsonDataWorker
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
from flightpath.widgets.tabs_closing import ClosingTabs
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.help_finder import HelpFinder
from flightpath.util.state import State


class MainWindow(QMainWindow): # pylint: disable=R0902, R0904
    """ Main GUI component. Does much of the MVC controller lifting. """


    def __init__(self):
        super().__init__()
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
        self.help_and_feedback = None
        self.help_and_feedback_layout = None
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
        if self.help_and_feedback:
            self.help_and_feedback.deleteLater()
            self.help_and_feedback = None
        self.help_and_feedback = ClosingTabs(main=self)
        #
        # state is a json file called ./.state. it is just a ui state
        # persistence tool with some configuration. not sure if it's a
        # keeper by needed today.
        #
        # when we do _load_state we are capturing the path to the state
        # file in the app's starting dir. then, if we find a {cwd:path}
        # key in state we chdir into it.
        #
        self.csvpath_config = CsvPath_Config()
        self.setWindowTitle("FlightPath Data • Data Preboarding Development")
        icon = QIcon(fiut.make_app_path(f"assets{os.sep}icons{os.sep}icon.png"))
        self.setWindowIcon(icon)
        self.threadpool = QThreadPool()
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

        self.help_and_feedback_layout = QVBoxLayout()
        self.help_and_feedback.setLayout(self.help_and_feedback_layout)
        self.help_and_feedback_layout.setContentsMargins(0, 0, 0, 0)

        self.main.addWidget(self.main_top)
        self.main.addWidget(self.help_and_feedback)
        self.main.setSizes( [1, 0] )
        self.assure_help_tab()

        self.sidebar = Sidebar(main=self)
        cw.addWidget(self.sidebar)
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
        d.deleteLater()

    def hide_rt_tabs(self) -> None:
        i = self.main_layout.currentIndex()
        if i in [0, 2]:
            self.rt_tab_widget.tabBar().hide()

    @property
    def help(self) -> QTextEdit:
        return self._help

    @help.setter
    def help(self, t:QTextEdit) -> None:
        self._help = t

    def _on_data_toolbar_show(self) -> None:
        self.content.data_view.toolbar.show()

    def _on_data_toolbar_hide(self) -> None:
        self.content.data_view.toolbar.hide()

    def _connects(self) -> None:
        """ some of the connects. may want to consolidate here
            and/or move consolidated to a helper connect class """
        self.rt_tab_widget.currentChanged.connect(self._on_rt_tab_changed)
        self.main_layout.currentChanged.connect(self._on_stack_change)
        self.welcome.clicked.connect(self.welcome.on_click)
        #
        # data_view's sampling toolbar
        #
        self.content.data_view.sampling.activated.connect(self.on_reload_data)
        self.content.data_view.rows.activated.connect(self.on_data_rows_changed)
        self.content.data_view.save_sample.clicked.connect(self.on_save_sample)
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

    #
    # -------------------------------
    # help stuff
    #

    def assure_help_tab(self) -> None:
        if self.help is None:
            self.help = QTextEdit()
            self.help.setObjectName("Help Content")
        t = self.help_and_feedback.findChild(QWidget, "Help Content")
        if t is None:
            self.help_and_feedback.addTab(self.help, "Help Content")
        self.help_and_feedback.setCurrentWidget(t)
        self.help_and_feedback.show()

    def get_help_tab_if(self) -> QWidget:
        t = self.help_and_feedback.findChild(QWidget, "Help Content")
        return t

    def get_help_tab_index_if(self) -> int:
        for i in range(self.help_and_feedback.count()):
            if self.help_and_feedback.tabText(i) == "Help Content":
                return i
        return -1

    def get_help_tab(self) -> QWidget:
        i = self.get_help_tab_index_if()
        if i == -1:
            h = QTextEdit()
            h.setObjectName("Help Content")
            self.help_and_feedback.addTab(h, "Help Content")
            return h
        return self.help_and_feedback.widget(i)

    def on_click_help(self) -> None:
        if self.is_showing_help():
            self.close_help()
        else:
            self.open_help()

    def open_help(self) -> None:
        self.main.setSizes([1, 1])

    def close_help(self) -> None:
        self.main.setSizes([1, 0])

    def is_showing_help(self) -> bool:
        ss = self.main.sizes()
        if ss is None:
            return False
        if len(ss) <= 1:
            return False
        return ss[1] > 0

    def on_click_named_files_help(self) -> None:
        md = HelpFinder(main=self).help("named_files/about.md")
        self.get_help_tab().setMarkdown(md)
        #self.help.setMarkdown(md)
        if not self.is_showing_help():
            self.on_click_help()

    def on_click_named_paths_help(self) -> None:
        md = HelpFinder(main=self).help("named_paths/about.md")
        #self.help.setMarkdown(md)
        self.get_help_tab().setMarkdown(md)
        if not self.is_showing_help():
            self.on_click_help()

    def on_click_archive_help(self) -> None:
        md = HelpFinder(main=self).help("archive/about.md")
        self.get_help_tab().setMarkdown(md)
        if not self.is_showing_help():
            self.on_click_help()

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
        """ loads a json file, updates main view + tabs """
        filepath, data, errors = worker_data   # pylint: disable=W0612
        self.content.json_source_view.open_file(path=filepath, data=data)
        self.progress_dialog.close()
        self.last_main = self.main_layout.currentIndex()
        #
        # show code/data tabs' panel
        #
        self.main_layout.setCurrentIndex(1)
        #
        # hide grid, source tabs
        #
        self.content.tab_widget.setTabVisible(0, False)
        self.content.tab_widget.setTabVisible(1, False)
        self.content.tab_widget.setTabVisible(2, False)
        self.content.tab_widget.setTabVisible(3, True)
        self._on_data_toolbar_hide()
        self._rt_tabs_hide()

    @Slot(tuple)
    def update_csvpath_views(self, worker_data):
        filepath, data, errors = worker_data # pylint: disable=W0612
        self.content.csvpath_source_view.open_file(path=filepath, data=data)
        self.progress_dialog.close()
        self.last_main = self.main_layout.currentIndex()
        #
        # show code/data tabs' panel
        #
        self.main_layout.setCurrentIndex(1)
        #
        # hide grid, source tabs
        #
        self.content.tab_widget.setTabVisible(0, False)
        self.content.tab_widget.setTabVisible(1, False)
        self.content.tab_widget.setTabVisible(2, True)
        self.content.tab_widget.setTabVisible(3, False)
        #
        # when csvpath source_view is visible we hide the sample tool bar
        #
        self.content.data_view.toolbar.hide()
        #
        # we show the right tabs in order to show the functions and docs
        #
        self._rt_tabs_show()

    @Slot(tuple)
    def update_views(self, worker_data):
        msg, lines, filepath, data, errors = worker_data # pylint: disable=W0612
        self.table_model = TableModel(data)
        self.content.data_view.display_data(self.table_model)
        self.content.source_view.open_file(filepath, lines)
        self.progress_dialog.close()
        self.last_main = self.main_layout.currentIndex()
        self.main_layout.setCurrentIndex(1)
        self.content.tab_widget.setTabVisible(0, True)
        self.content.tab_widget.setTabVisible(1, True)
        self.content.tab_widget.setTabVisible(2, False)
        self.content.tab_widget.setTabVisible(3, False)
        self.content.tab_widget.setCurrentIndex(0)
        #
        # when  data _view is visible we show the sample tool bar
        #
        self.content.data_view.toolbar.show()
        #
        # hide right tabs because we don't need csvpath helpers when looking
        # at data
        #
        self._rt_tabs_hide()

    def on_data_rows_changed(self) -> None:
        t = self.content.data_view.rows.currentText()
        if t == "All lines":
            #
            # set the sampling options to first-n and remove or disable others
            #
            self.content.data_view.sampling.setCurrentIndex(0)
            self.content.data_view.sampling.model().item(0).setEnabled(False)
            self.content.data_view.sampling.model().item(1).setEnabled(False)
            self.content.data_view.sampling.model().item(2).setEnabled(False)
            #
            # select first-n
            #
        else:
            self.content.data_view.sampling.model().item(0).setEnabled(True)
            self.content.data_view.sampling.model().item(1).setEnabled(True)
            self.content.data_view.sampling.model().item(2).setEnabled(True)
            #
            # add/enable all sampling options
            #
        #
        # tell data to reload. the worker will known what to do about
        # sampling and number of lines
        #
        self.read_validate_and_display_file()

    def read_validate_and_display_file(self):
        info = QFileInfo(self.selected_file_path)
        #
        # TODO: consolidate below
        #
        # pylint thinks csv_file_extensions doesn't support membership tests but it is list[str]. :/
        if info.isFile() and info.suffix() in self.csvpath_config.csv_file_extensions: # pylint: disable=E1135
            worker = GeneralDataWorker(
                self.selected_file_path,
                self,
                rows=self.content.data_view.rows.currentText(),
                sampling=self.content.data_view.sampling.currentText()
            )
            worker.signals.finished.connect(self.update_views)
            worker.signals.messages.connect(self.statusBar().showMessage)

            self.progress_dialog = QProgressDialog("Loading...", None, 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setValue(0)
            self.progress_dialog.setMinimumDuration(300)  # show if task takes more than 300ms
            self.threadpool.start(worker)
        # pylint thinks csvpath_file_extensions doesn't support membership tests but it is list[str]. :/
        elif info.isFile() and info.suffix() in self.csvpath_config.csvpath_file_extensions: # pylint: disable=E1135
            worker = CsvpathFileWorker(self.selected_file_path, self)
            worker.signals.finished.connect(self.update_csvpath_views)
            worker.signals.messages.connect(self.statusBar().showMessage)

            self.progress_dialog = QProgressDialog("Loading...", None, 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setValue(0)
            self.progress_dialog.setMinimumDuration(300)  # show if task takes more than 300ms
            self.threadpool.start(worker)

        elif info.isFile() and info.suffix() == "json":
            worker = JsonDataWorker(self.selected_file_path, self)
            worker.signals.finished.connect(self.update_json_views)
            worker.signals.messages.connect(self.statusBar().showMessage)

            self.progress_dialog = QProgressDialog("Loading...", None, 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setValue(0)
            self.progress_dialog.setMinimumDuration(300)  # show if task takes more than 300ms
            self.threadpool.start(worker)
        else:
            self.clear_views()

    @Slot(QModelIndex)
    def on_tree_click(self, index):
        if not index.isValid():
            return
        try:
            source_index = self.sidebar.proxy_model.mapToSource(index)
            if not source_index.isValid():
                return
            #
            # do we need to verify that we're looking at a csvpath file?
            #
            if self.sidebar.last_file_index and not self.content.csvpath_source_view.saved:
                #
                # double check dialog. if accepted, clear with: saved = True
                #
                path = self.content.csvpath_source_view.path
                if path.startswith(self.state.cwd):
                    path = path[len(self.state.cwd) + 1:]
                confirm = QMessageBox.question(
                    self,
                    "Close file",
                    f"Close {path} without saving?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if confirm == QMessageBox.No:
                    #
                    # set the file tree selected back to the orig
                    # TODO: this works within one parent node, but doesn't work in another parent dir.
                    # leaving it for now because it's not a huge bug and it can get done after higher
                    # priorities.
                    #
                    self.sidebar.file_navigator.clearSelection()
                    selection_model = self.sidebar.file_navigator.selectionModel()
                    selection_model.select(self.sidebar.last_file_index,
                            QItemSelectionModel.Select | QItemSelectionModel.Rows)
                    return
                #
                # set the view to be saved and clear any "+" in the tab name.
                #
                self.main.content.csvpath_source_view.reset_saved()
                #
                #
                #
            file_info = self.sidebar.file_model.fileInfo(source_index)
            self.selected_file_path = file_info.filePath()
            self.read_validate_and_display_file()
            self.statusBar().showMessage(f"  {self.selected_file_path}")
            #
            # store the index for use in the case the user clicks off the current file
            # but then responds no to a confirm box.
            #
            self.sidebar.last_file_index = index
        except Exception as e: # pylint: disable=W0718
            #
            # not clear what exception might be caught here. we have had memory faults
            # but those were fixed.
            #
            print(f"Error handling click: {e}")


    def on_named_file_tree_click(self, index):
        self.selected_file_path = Path(self.sidebar_rt_top.model.filePath(index))
        self.read_validate_and_display_file()

    def on_named_paths_tree_click(self, index):
        self.selected_file_path = Path(self.sidebar_rt_mid.model.filePath(index))
        self.read_validate_and_display_file()

    def on_archive_tree_click(self, index):
        self.selected_file_path = Path(self.sidebar_rt_bottom.model.filePath(index))
        self.read_validate_and_display_file()

    def clear_views(self):
        self.table_model = TableModel([])
        self.content.data_view.clear(self.table_model)
        self.content.source_view.clear()

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
            self.sidebar.last_file_index
            and not self.content.csvpath_source_view.saved
            and self.main_layout.currentIndex() == 1
            and self.content.tab_widget.currentIndex() == 2
        ):
            reply = QMessageBox.question(self, 'Confirm Close',
                                     'Are you sure you want to quit without saving?',
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()

def run():
    app = QApplication(sys.argv)
    app.setApplicationName("FlightPath Data Automation Development")
    app.setStyle("Fusion")

    window = MainWindow()
    #
    # careful, this was throwing an error at one point, but is currently
    # commented mainly because a smaller window is easier.
    #
    #window.showMaximized()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run()
