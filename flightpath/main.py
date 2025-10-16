# pylint: disable=C0302
""" The main window and application startup (at bottom, below classes) """
import sys
import os
import csv

from pathlib import Path

import darkdetect

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
    QMessageBox,
    QTextEdit,
    QLabel,
    QMenuBar,
    QPlainTextEdit
)
from PySide6.QtGui import QIcon, QAction # pylint: disable=E0611
from PySide6.QtCore import ( # pylint: disable=E0611
    Qt,
    QFileInfo,
    QThreadPool,
    QThread,
    Slot,
    QSize,
    QItemSelectionModel,
    QRunnable,
    QModelIndex,
    QCoreApplication,
    QTimer
)

from csvpath import CsvPaths
from csvpath.util.config import Config as CsvPathConfig
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos

from flightpath.workers.md_worker import MdWorker
from flightpath.workers.csvpath_file_worker import CsvpathFileWorker
from flightpath.workers.general_data_worker import GeneralDataWorker
from flightpath.workers.json_data_worker import JsonDataWorker
from flightpath.widgets.panels.csvpath_viewer import CsvpathViewer
from flightpath.widgets.panels.md_viewer import MdViewer
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
from flightpath.util.log_utility import LogUtility as lout
from flightpath.util.os_utility import OsUtility as osut
from flightpath.util.message_utility import MessageUtility as meut
from flightpath.util.style_utils import StyleUtility as stut

from flightpath.util.state import State
from flightpath.inspect.inspector import Inspector
from flightpath.util.html_generator import HtmlGenerator
from flightpath.editable import EditStates
from flightpath_server.main import Main as ServerMain

from flightpath.workers.run_worker import RunWorker
from flightpath.workers.precache_worker import PreCacheWorker

def run():
    #
    # if --server-mode:
    #    - check for server mode key
    #    - if key found, start a FlightPath Server
    #
    from flightpath.util.gate_guard import GateGuard
    mode = GateGuard.has_ticket()
    if mode is True:
        #
        # start server here!
        #
        print(GateGuard.ART)
        main = ServerMain()
        main.serve()
        return
    else:
        print(
"""
Loading FlightPath Data.

To start an instance of FlightPath Server, pass --server-mode when you start FlightPath from the command line

For more information about FlightPath Server see https://www.flightpathdata.com.
"""
        )
    #
    # otherwise continue to load FlightPath Data
    #
    from flightpath.hidden import Hidden
    Hidden()
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


class MainWindow(QMainWindow): # pylint: disable=R0902, R0904
    """ Main GUI component. Does much of the MVC controller lifting. """

    TITLE = "FlightPath • Data Preboarding Development and Operations"


    def __init__(self):
        super().__init__()
        #
        # please close will be True if the user chooses not to pick a
        # working directory on first startup. This is not expected to
        # happen, but if it did, we need the application initalization
        # code to not put the app into exec.
        #
        self.main = None
        self.main_top = None
        self.main_layout = None
        self.welcome = None
        self.content = None
        self.config = None
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
        self._csvpath_config = None
        self.threadpool = None
        self._selected_file_path = None
        self.last_main = None
        self.build_number = None
        self.progress_dialog = None # not sure we need this as a member, but it is used as one atm.
        #
        # TODO: why do we create state twice?
        #
        self.state = None
        #
        # get log setup. the level comes from the state. that leaves us
        # in the dark till we obtain state, but that should be fine.
        #
        self.logger = None
        #
        # if we fail to / chose not to set a cwd we will close the app
        #
        self.please_close = False
        #
        # at first launch we want to be sure to call show() on child windows
        # after we call show on the main window; otherwise, on Windows, at
        # least, on launch we get a popcorn of windows before things settle
        # down.
        #
        self.launch_shows = []

        if not self.state_check():
            return
        self.load_state_and_cd()
        #
        # after this we show the other first shows()
        #
        self.show()
        #
        # do child shows here?
        #
        for _ in self.launch_shows:
            _.show()
        #
        # when we're done launching set this to None to make sure we
        # call show() right away.
        #
        self.launch_shows = None
        #
        # react to light/dark changes
        #
        QCoreApplication.instance().styleHints().colorSchemeChanged.connect(self.on_color_scheme_changed)
        if darkdetect.isDark():
            self.on_color_scheme_changed()

        #
        # kickoff a precache worker to collect some info about files
        #
        QTimer.singleShot(1000, self._run_precacher)


    def _run_precacher(self) -> None:
        try:
            worker = PreCacheWorker(self.state.cwd)
            if self.threadpool:
                worker.signals.messages.connect(self.statusBar().showMessage)
                self.threadpool.start(worker, priority=QThread.LowestPriority.value)
        except Exception:
            import traceback
            print(traceback.format_exc())


    def show_now_or_later(self, showable) -> None:
        if not hasattr(showable, "show"):
            raise ValueError(f"Cannot show a {showable}")
        if self.launch_shows is None:
            showable.show()
        else:
            self.launch_shows.append(showable)


    def on_color_scheme_changed(self) -> None:
        QCoreApplication.instance().setStyle("Fusion")
        #
        # splitters apparently need special handling.
        #
        if darkdetect.isDark():
            s = "QSplitter::handle { background-color: #535353;  margin:1px; }"
            self.centralWidget().setStyleSheet(s)
            self.rt_col_helpers.setStyleSheet(s)
            self.rt_col.setStyleSheet(s)
            self.main.setStyleSheet(s)
        if darkdetect.isLight():
            s = "QSplitter::handle { background-color: #f3f3f3;  margin:1px; }"
            self.centralWidget().setStyleSheet(s)
            self.rt_col_helpers.setStyleSheet(s)
            self.rt_col.setStyleSheet(s)
            self.main.setStyleSheet(s)
        #
        # schedule an update for the splitters
        #
        self.rt_col_helpers.update()
        self.rt_col.update()
        self.main.update()
        self.centralWidget().update()
        #
        # handle the file trees specially. there is probably a better way.
        #
        self.sidebar_rt_top.update_style()
        self.sidebar_rt_mid.update_style()
        self.sidebar_rt_bottom.update_style()
        #
        # walk through the open files
        #
        for t in taut.tabs(self.content.tab_widget):
            stut.set_editable_background(t)

    def state_check(self) -> bool:
        self.state = State()
        if self.state.has_cwd():
            ...
        else:
            self.state.pick_cwd(self)
            if self.state.has_cwd():
                ...
            else:
                QCoreApplication.instance().exit()
                #
                # I'm not 100% clear why exit() isn't enough, but it needs a little help.
                # this flag works fine and seems good.
                #
                self.please_close = True
                return False
        self.load_state_and_cd()
        self.statusBar().showMessage(f"  Project changed to: {self.state.cwd}")
        return True

    @property
    def csvpath_config(self) -> CsvPathConfig:
        if self._csvpath_config is None:
            paths = CsvPaths()
            self._csvpath_config = paths.config
        return self._csvpath_config

    def clear_csvpath_config(self) -> None:
        self._csvpath_config = None

    @property
    def selected_file_path(self) -> str:
        return self._selected_file_path

    @selected_file_path.setter
    def selected_file_path(self, path:str) -> None:
        self._selected_file_path = path

    def log(self, msg:str) -> None:
        if self.logger is None:
            if self.state.debug == "on":
                self.logger = lout.logger(self.state)
            else:
                self.logger = False
        if self.logger:
            self.logger.debug(msg)

    def load_state_and_cd(self) -> None:
        """ sets the project directory into .flightpath file, cds to project dir, and reloads UI. """
        self.state.load_state_and_cd(self)
        #
        # if we have env vars set them for this process
        #
        self.state.load_env()
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
        icon = QIcon(fiut.make_app_path(f"assets{os.sep}icons{os.sep}icon.ico"))
        self.setWindowIcon(icon)
        #
        #
        self.threadpool = QThreadPool.globalInstance()
        #
        # this should be Path() not None?
        #
        self.selected_file_path = Path()
        central_widget = self.takeCentralWidget()
        if central_widget:
            central_widget.deleteLater()
        central_widget = QSplitter(self)
        central_widget.setObjectName("central_widget")
        central_widget.setHandleWidth(3)
        central_widget.setStyleSheet("QSplitter::handle { background-color: #f3f3f3;  margin:1px; }")
        self.setCentralWidget(central_widget)
        self._setup_central_widget()
        #
        # tracks the most recent main_layout index so we can return
        # from config or wherever.
        #
        self.last_main = 0
        self.statusBar().showMessage(f"  Working directory: {self.state.cwd}")

        build_number = fiut.read_string(fiut.make_app_path(f"assets{os.sep}build_number.txt")).strip()
        if self.build_number is None:
            self.build_number = QLabel()
            self.build_number.setObjectName("build_number")
            self.build_number.setStyleSheet("QLabel {font-size:10px;color:#999}")
            self.statusBar().addPermanentWidget(self.build_number, 0)
        self.build_number.setText(build_number)

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
        #
        #
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
        #cw.addWidget(self.main)
        cw.addWidget(self.main)
        #
        # put a tab widget into 3rd column of splitter.
        # 1st tab has the rt_col vert spliter with three file trees
        # 2nd tab has the functions, qualifiers, and maybe docs?
        # hide 2nd tab unless csvpath file is open
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

    def renew_sidebar_named_files(self) -> None:
        d = self.sidebar_rt_top
        self.sidebar_rt_top = SidebarNamedFiles(main=self, config=self.csvpath_config, role=3)
        self.rt_col.replaceWidget(0, self.sidebar_rt_top)
        d.deleteLater()

    def renew_sidebar_named_paths(self) -> None:
        d = self.sidebar_rt_mid
        self.sidebar_rt_mid = SidebarNamedPaths(main=self, config=self.csvpath_config, role=3)
        self.rt_col.replaceWidget(1, self.sidebar_rt_mid)
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
        self.show_now_or_later( self.content.toolbar )

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
        self.content.toolbar.file_info.clicked.connect(self.on_file_info)
        #
        #
        #
        self.sidebar.file_navigator.clicked.connect(self.on_tree_click)
        #
        # rt-side trees
        #
        #self.sidebar_rt_top.view.clicked.connect(self.on_named_file_tree_click)
        #self.sidebar_rt_mid.view.clicked.connect(self.on_named_paths_tree_click)
        #self.sidebar_rt_bottom.view.clicked.connect(self.on_archive_tree_click)
        #
        # config stuff
        #
        self.config.toolbar.button_close.clicked.connect(self.close_config)
        self.config.toolbar.button_cancel_changes.clicked.connect(self.cancel_config_changes)
        self.config.toolbar._button_save.clicked.connect(self.save_config_changes)
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
        print(f"rt_tab_changed. not reacting.")
        ...

    def _rt_tabs_hide(self) -> None:
        self.rt_tab_widget.tabBar().setCurrentIndex(0)
        self.rt_tab_widget.tabBar().hide()

    def _rt_tabs_show(self) -> None:
        self.show_now_or_later(self.rt_tab_widget.tabBar())
        #self.rt_tab_widget.tabBar().show()

    def question_config_close(self) -> None:
        if (
            self.config and
            self.config.ready is True and
            self.config.toolbar._button_save.isEnabled()
        ):
            save = QMessageBox.question(
                self,
                "Config changed",
                "Save config changes?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if save == QMessageBox.Yes:
                self.save_config_changes()
            self.reset_config_toolbar()

    def _on_stack_change(self) ->None:
        i = self.main_layout.currentIndex()
        #
        # if i == 2 (Config) we have to check if the config has changed. if it has
        # and we switch away work could be lost. we need to confirm w/user that is
        # ok.
        #
        if i != 2:
            self.question_config_close()
            """
            if (
                self.config and
                self.config.ready is True and
                self.config.toolbar._button_save.isEnabled()
            ):
                save = QMessageBox.question(
                    self,
                    "Config changed",
                    "Save config changes?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if save == QMessageBox.Yes:
                    self.save_config_changes()
                self.reset_config_toolbar()
            """
        if i in [0, 2]:
            self._rt_tabs_hide()
        else:
            #
            # we're switching to data or a csvpath file. that means we show the helper tab
            # and make both visible in the tabbar. if we haven't shown the tabbar before we
            # don't have a populated helper tree, so we need to get on that.
            #
            if self.launch_shows is not None:
                self.launch_shows.append(self._rt_tabs_show)
            else:
                self._rt_tabs_show()
            if self.rt_col_helpers.count() == 0:
                self.sidebar_functs = SidebarFunctions(main=self)
                self.rt_col_helpers.addWidget(self.sidebar_functs)
                self.sidebar_docs = SidebarDocs(main=self, functions=self.sidebar_functs.functions)
                self.rt_col_helpers.addWidget(self.sidebar_docs)

    @Slot(tuple)
    def update_json_views(self, worker_data):
        try:
            filepath, data, editable = worker_data   # pylint: disable=W0612
            if self.progress_dialog:
                self.progress_dialog.close()
            if isinstance( data, Exception ):
                meut.message(icon=QMessageBox.Critical, title="File opening error", msg=f"Error: {data}")
                return
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
        except Exception as e:
            print(f"Error opening json: {type(e)}: {e}")
        print(f"main: done with update_json_views, tabs: {self.content.tab_widget}")
        print(f"main: done with update_json_views, tabs: {self.content.tab_widget.count()}")
        print(f"main: done with update_json_views, main_layout: {self.main_layout}")
        print(f"main: done with update_json_views, main_layout index: {self.main_layout.currentIndex()}")


    @Slot(tuple)
    def update_md_views(self, worker_data):
        filepath, data, editable = worker_data # pylint: disable=W0612
        if self.progress_dialog:
            self.progress_dialog.close()
        if isinstance( data, Exception ):
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("File opening error")
            msg_box.setText(f"Error: {data}")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
            return
        self.last_main = self.main_layout.currentIndex()
        #
        # show code/data tabs' panel
        #
        self.main_layout.setCurrentIndex(1)
        self.content.toolbar.disable()
        #
        #
        #
        view = taut.find_tab(self.content.tab_widget, filepath)
        if view is None:
            editable = editable if editable is not None else EditStates.EDITABLE
            #
            # the displaying:bool argument determines if .md or .txt. odd, but workable.
            # it doesn't affect the editability of the file.
            #
            displaying = True
            #
            # being over careful because this is just a fix, not new work
            #
            try:
                _, ext = os.path.splitext(filepath)
                if ext == "txt":
                    displaying = False
            except Exception:
                ...
            view = MdViewer(main=self, editable=editable, displaying=displaying)
            view.setObjectName(filepath)
            #
            # TODO: oddly, we use the worker to open and then just open again
            # this is a legacy of something validation related. it exists
            # in csvpath and json files too.
            #
            view.open_file(path=filepath, data=data)
            self.content.tab_widget.addTab(view, os.path.basename(filepath) )
            save = "cmd-s" if osut.is_mac() else "ctrl-s"
            shortcuts = f"{save} to save"
            i = taut.find_tab(self.content.tab_widget, filepath)
            self.content.tab_widget.setTabToolTip(i[0], shortcuts)
        else:
            view = view[1]
        view.editable = editable if editable else EditStates.EDITABLE
        taut.select_tab(self.content.tab_widget, view)
        #
        # we show the right tabs because we may be showing
        # information relating to them in some way. if this
        # feels odd in practice we can be more careful in
        # when/if we do it.
        #
        self._rt_tabs_show()


    @Slot(tuple)
    def update_csvpath_views(self, worker_data):
        filepath, data, editable = worker_data # pylint: disable=W0612
        if self.progress_dialog:
            self.progress_dialog.close()
        if isinstance( data, Exception ):
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("File opening error")
            msg_box.setText(f"Error: {data}")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
            return
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
            editable = editable if editable is not None else EditStates.EDITABLE
            csvpath_view = CsvpathViewer(main=self, editable=editable)
            csvpath_view.setObjectName(filepath)
            csvpath_view.open_file(path=filepath, data=data)
            self.content.tab_widget.addTab(csvpath_view, os.path.basename(filepath) )

            save = "cmd-s" if osut.is_mac() else "ctrl-s"
            run = "cmd-r" if osut.is_mac() else "ctrl-r"
            shortcuts = f"{save} to save, {run} to run"
            i = taut.find_tab(self.content.tab_widget, filepath)
            self.content.tab_widget.setTabToolTip(i[0], shortcuts)

        else:
            csvpath_view = csvpath_view[1]
        csvpath_view.editable = editable if editable else EditStates.EDITABLE
        taut.select_tab(self.content.tab_widget, csvpath_view)
        #
        # we show the right tabs in order to show the functions and docs
        #
        self._rt_tabs_show()

    @Slot(tuple)
    def update_views(self, worker_data):
        msg, lines, filepath, data, lines_to_take = worker_data # pylint: disable=W0612
        if self.progress_dialog:
            self.progress_dialog.close()
        if isinstance( lines, Exception ):
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("File opening error")
            msg_box.setText(f"Error: {lines}")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
            return
        table_model = TableModel(data)
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
        data_view.display_data(table_model)
        #
        # when  data _view is visible we show the sample tool bar
        #
        self.content.toolbar.enable()
        self.show_now_or_later(self.content.toolbar)
        #self.content.toolbar.show()
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

    def read_validate_and_display_file(self, editable=EditStates.EDITABLE, *, finished_callback=None) -> QRunnable:
        return self.read_validate_and_display_file_for_path(self.selected_file_path, editable=editable, finished_callback=finished_callback)

    def read_validate_and_display_file_for_path(self, path:str, editable=EditStates.EDITABLE, *, finished_callback=None) -> QRunnable:
        print(f"read_validate_and_display_file_for_path 1")
        #
        # callbacks passed into this method should be watched closely. the find data by ref dialog
        # had trouble getting them to behave correctly.
        #
        info = QFileInfo(path)
        #
        # TODO: consolidate below
        #
        worker = None
        nos = Nos(path)
        isfile = nos.isfile()
        if isfile and info.suffix() in self.csvpath_config.get(section="extensions", name="csv_files"): # pylint: disable=E1135
            worker = GeneralDataWorker(
                path,
                self,
                rows=self.content.toolbar.rows.currentText(),
                sampling=self.content.toolbar.sampling.currentText(),
                delimiter=self.content.toolbar.delimiter_char(),
                quotechar=self.content.toolbar.quotechar_char()
            )
            worker.signals.finished.connect(self.update_views)
            if finished_callback is not None:
                worker.signals.finished.connect(finished_callback)
            worker.signals.messages.connect(self.statusBar().showMessage)
            self.progress_dialog = QProgressDialog("Loading...", None, 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setValue(0)
            self.progress_dialog.setMinimumDuration(400)
            self.threadpool.start(worker)
        elif isfile and info.suffix() in self.csvpath_config.get(section="extensions", name="csvpath_files"): # pylint: disable=E1135
            worker = CsvpathFileWorker(path, self, editable=editable)
            worker.signals.finished.connect(self.update_csvpath_views)
            if finished_callback is not None:
                worker.signals.finished.connect(finished_callback)
            worker.signals.messages.connect(self.statusBar().showMessage)
            self.progress_dialog = QProgressDialog("Loading...", None, 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setValue(0)
            self.progress_dialog.setMinimumDuration(400)
            self.threadpool.start(worker)
        elif isfile and info.suffix() == "json":
            worker = JsonDataWorker(path, self, editable=editable)
            if finished_callback is not None:
                #
                # this callback should work, but even when clearly wired right it
                # doesn't seem to actually get called. no idea what's up. :/
                #
                worker.signals.finished.connect(finished_callback)
            worker.signals.finished.connect(self.update_json_views)
            worker.signals.messages.connect(self.statusBar().showMessage)
            self.progress_dialog = QProgressDialog("Loading...", None, 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setValue(0)
            self.progress_dialog.setMinimumDuration(400)
            self.threadpool.start(worker)
        elif isfile and info.suffix() in ["md", "html", "txt"]:
            #
            # txt could be set in csv extensions. probably not, but possible. we
            # don't need these to be configurable at this time.
            #
            worker = MdWorker(path, self, editable=editable)
            worker.signals.finished.connect(self.update_md_views)
            if finished_callback is not None:
                worker.signals.finished.connect(finished_callback)
            worker.signals.messages.connect(self.statusBar().showMessage)
            self.progress_dialog = QProgressDialog("Loading...", None, 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setValue(0)
            self.progress_dialog.setMinimumDuration(400)
            self.threadpool.start(worker)
        elif not info.isFile():
            meut.message(title="File opening error", msg=f"Cannot open {path}")
        else:
            print("Error: main.read_validate_and_display_file_for_path: cannot open file")
            self.clear_views()
        return worker


    def run_paths(self, *,
        method:str,
        named_paths_name:str,
        named_file_name:str,
        template:str
    ) -> None:
        runner = RunWorker(
            method=method,
            named_paths_name=named_paths_name,
            named_file_name=named_file_name,
            template=template
        )
        #
        # clear any existing logs to .bak. we have to shutdown to be sure that the
        # file is released. that's not a problem because it is CsvPath logging, not
        # FlightPath logging.
        #
        lout.rotate_log(self.state.cwd, self.csvpath_config)
        #
        #
        #
        runner.signals.finished.connect(self._display_log)
        runner.signals.messages.connect(self.statusBar().showMessage)
        self.threadpool.start(runner)

    @Slot(tuple)
    def _display_log(self, t:tuple[str]) -> None:
        log = QWidget()
        log.setObjectName("Log")
        self.helper.help_and_feedback.addTab(log, "Log")
        #
        # the logs tab should be the first showing, at least unless/until
        # we add more run results tabs.
        #
        i = self.helper.help_and_feedback.count()
        self.helper.help_and_feedback.setCurrentIndex(i-1)

        layout = QVBoxLayout()
        log.setLayout(layout)
        view = QPlainTextEdit()
        log_lines = lout.get_log_content(self.csvpath_config)
        view.setPlainText(log_lines)
        view.setReadOnly(True)
        layout.addWidget(view)
        layout.setContentsMargins(0, 0, 0, 0)
        #
        # clear the logging; basically remove the handler.
        #
        lout.clear_logging(t[1])
        #
        # show log. do this even if nothing much to show
        #
        if not self.helper.is_showing_help():
            self.helper.on_click_help()
        #
        # update the sidebar so we can see the results
        #
        # TODO: we were recreating all trees. bad idea due to slow refresh from remote.
        # but worked. refreshing named_files is probably fair, but that's
        # also tricky because we'd want to recreate the opened/closed state of the folders
        # and if we did that the refresh might slow down potentially a lot. so long-term,
        # seems like we should capture what is registered and manually add it.
        #
        self.renew_sidebar_archive()




    @Slot(QModelIndex)
    def on_tree_click(self, index):
        if not index.isValid():
            return
        source_index = self.sidebar.proxy_model.mapToSource(index)
        if not source_index.isValid():
            return

        file_info = self.sidebar.file_model.fileInfo(source_index)
        #
        # file_info.filePath sometimes allows a // to prefix the path on Mac. not
        # sure why that should be, keeping in mind we don't populate the paths in the
        # file view by hand. regardless for now, just switching to canonical and
        # moving on.
        #
        #self.selected_file_path = file_info.filePath()
        self.selected_file_path = file_info.canonicalFilePath()
        nos = Nos(self.selected_file_path)
        if not nos.isfile():
            return
        info = QFileInfo(self.selected_file_path)
        editable = info.suffix() in self.csvpath_config.get(section="extensions", name="csvpath_files")
        editable = editable or info.suffix() in ["json", "md", "txt"]
        if editable is True:
            editable = EditStates.EDITABLE
        else:
            editable = EditStates.UNEDITABLE
        self.read_validate_and_display_file(editable=editable)
        self.statusBar().showMessage(f"  {self.selected_file_path}")
        #
        # store the index for use in the case the user clicks off the current file
        # but then responds no to a confirm box.
        #
        self.sidebar.last_file_index = index

    def clear_views(self):
        self.content.close_all_tabs()

    def on_help_click(self) -> None:
        ss = self.main.sizes()
        if ss[1] > 0:
            self.main.setSizes([1, 0])
        else:
            self.main.setSizes([4, 1])

    def is_writable(self, path) -> bool:
        return fiut.is_writable_dir(path)

    def on_set_cwd_click(self):
        caption = "FlightPath requires a project directory. Please pick one."
        home = str(Path.home())
        path = QFileDialog.getExistingDirectory(
                self,
                caption,
                options=QFileDialog.Option.ShowDirsOnly,
                dir=home
        )
        if path:
            if self.is_writable(path):
                self.state.cwd = path
            else:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setWindowTitle("Not writable")
                msg_box.setText(f"{path} is not a writable location. Please pick another.")
                msg_box.setStandardButtons(QMessageBox.Ok)
                msg_box.exec()
                self.on_set_cwd_click()


    def on_reload_data(self) -> None:
        self.read_validate_and_display_file()

    def on_set_delimiter(self) -> None:
        self.read_validate_and_display_file()

    def on_set_quotechar(self) -> None:
        self.read_validate_and_display_file()

    def on_raw_source(self) -> None:
        index = self.content.tab_widget.currentIndex()
        t = self.content.tab_widget.widget(index)
        t.toggle_grid_raw()

    def on_file_info(self) -> None:
        index = self.content.tab_widget.currentIndex()
        t = self.content.tab_widget.widget(index)
        path = t.objectName()

        inspector = Inspector(main=self, filepath=path)
        inspector.sample_size=50
        inspector.from_line=1

        t = fiut.make_app_path(f"assets{os.sep}help{os.sep}templates{os.sep}file_details.html")
        html = HtmlGenerator.load_and_transform(t, inspector.info)

        info = taut.find_tab(self.helper.help_and_feedback, "File Info")
        if info is None:
            info = QWidget()
            info.setObjectName("FileInfo")
            self.helper.help_and_feedback.addTab(info, "File Info")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        info.setLayout(layout)
        te = QTextEdit()
        layout.addWidget(te)
        te.setText(html)
        taut.select_tab_widget(self.helper.help_and_feedback, info)
        self.config.show_help()



    def on_save_sample(self) -> None:
        index = self.content.tab_widget.currentIndex()
        t = self.content.tab_widget.widget(index)
        path = t.objectName()
        source = path
        name = None
        nos = Nos(path)
        if path.endswith("xlsx") or path.endswith("xls"):
            path = path[0:path.rfind(".")]
            path = f"{path}.csv"
        if nos.isfile():
            name = os.path.basename(path)
            path = os.path.dirname(path)
        else:
            name = "sample.csv"
        #
        # get current tab data
        #
        l = t.layout()
        w = l.itemAt(0).widget()
        m = w.model()
        data = m.get_data()
        #
        #
        #
        path = self.save_sample(path=path, name=name, data=data)
        #
        # reload views with new file
        # set the file tree to highlight the new file
        #
        if path is not None:
            self.read_validate_and_display_file_for_path(path=path)
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

        self.content.tab_widget.close_tab(source)


    def save_sample(self, *, path:str, name:str, data:str) -> str:
        #
        # if the app entered a subpath somehow pull it off name, into path, and check if it exists
        #
        if name.find(os.sep):
            path = os.path.join(path, name)
            name = os.path.basename(path)
            path = os.path.dirname(path)
        #
        # if we're not saving to the root check that we have a location
        #
        if path.strip() != "":
            nos = Nos(path)
            if not nos.exists():
                nos.makedirs()
        #
        # get user's file name and save
        #
        dialog = QInputDialog()
        dialog.setFixedSize(QSize(420, 125))
        dialog.setLabelText("Enter a name for the sample file:")
        dialog.setTextValue(name)
        ok = dialog.exec()
        new_name = dialog.textValue()
        #
        #
        #
        if ok and new_name and new_name.strip() != "":
            if not new_name.endswith(".csv"):
                new_name = f"{new_name}.csv"
            #
            # do the same subpath rejiggering in case the user added a subpath to name
            #
            if new_name.find(os.sep):
                path = os.path.join(path, new_name)
                new_name = os.path.basename(path)
                path = os.path.dirname(path)
            if path.strip() != "":
                nos = Nos(path)
                if not nos.exists():
                    nos.makedirs()
            #
            # minimal change to help us not overwrite
            #
            path = fiut.deconflicted_path(path, new_name)
            with DataFileWriter(path=path) as file: # pylint: disable=E0110
                writer = csv.writer(file.sink)
                writer.writerows(data)
            return path
        else:
            return None

    def open_config(self):
        if self.main_layout.currentIndex() != 2:
            self.last_main = self.main_layout.currentIndex()
            self.main_layout.setCurrentIndex(2)
            self.cancel_config_changes()
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

    def reset_config_toolbar(self):
        if hasattr(self, "config") and self.config:
            self.config.reset_config_toolbar()

    def cancel_config_changes(self):
        # exp
        self.csvpath_config.reload()
        #
        self.config.config_panel.populate_all_forms()
        self.reset_config_toolbar()

    def save_config_changes(self):
        try:
            self.config.config_panel.save_all_forms()
            self.config.config_panel.populate_all_forms()
            self.reset_config_toolbar()
        except Exception as e:
            meut.message(title="Error saving config", msg=f"Error saving config: {e}")

    def on_config_changed(self):
        if hasattr(self, "config") and self.config:
            self.config.toolbar.button_close.setEnabled(False)
            self.config.toolbar.button_cancel_changes.setEnabled(True)
            self.config.toolbar.enable_save()

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


if __name__ == "__main__":
    run()
