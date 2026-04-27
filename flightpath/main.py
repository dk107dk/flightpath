from typing import Callable
from pathlib import Path
import sys
import os
import csv
import traceback
import json
import darkdetect

from PySide6.QtWidgets import (  # pylint: disable=E0611
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QStackedLayout,
    QInputDialog,
    QSplitter,
    QTabWidget,
    QSizePolicy,
    QMessageBox,
    QTextEdit,
    QLabel,
    QPlainTextEdit,
)
from PySide6.QtGui import QIcon  # pylint: disable=E0611
from PySide6.QtCore import (  # pylint: disable=E0611
    Qt,
    QFileInfo,
    QThreadPool,
    QThread,
    Slot,
    QSize,
    QRunnable,
    QCoreApplication,
    QTimer,
)

from csvpath import CsvPaths
from csvpath.util.config import Config as CsvPathConfig
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos
from csvpath.util.path_util import PathUtility as pathu

from flightpath_server.main import Main as ServerMain

from flightpath.hidden import Hidden
from flightpath.reactor import Reactor

from flightpath.workers.md_worker import MdWorker
from flightpath.workers.csvpath_file_worker import CsvpathFileWorker
from flightpath.workers.general_data_worker import GeneralDataWorker
from flightpath.workers.json_data_worker import JsonDataWorker
from flightpath.workers.run_worker import RunWorker
from flightpath.workers.precache_worker import PreCacheWorker

from flightpath.widgets.panels.csvpath_viewer import CsvpathViewer
from flightpath.widgets.panels.md_viewer import MdViewer
from flightpath.widgets.panels.data_viewer import DataViewer
from flightpath.widgets.panels.json_viewer_2 import JsonViewer2
from flightpath.widgets.panels.json_viewer import JsonViewer
from flightpath.widgets.table_model import TableModel
from flightpath.widgets.sidebars.sidebar import Sidebar
from flightpath.widgets.sidebars.sidebar_named_files import SidebarNamedFiles
from flightpath.widgets.sidebars.sidebar_named_paths import SidebarNamedPaths
from flightpath.widgets.sidebars.sidebar_archive import SidebarArchive
from flightpath.widgets.pages.welcome import Welcome
from flightpath.widgets.pages.content import Content
from flightpath.widgets.pages.config import Config
from flightpath.widgets.help.helper import Helper
from flightpath.widgets.ai.query_tab import QueryTabWidget

from flightpath.util.help_finder import HelpFinder
from flightpath.util.gate_guard import GateGuard
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.tabs_utility import TabsUtility as taut
from flightpath.util.log_utility import LogUtility as lout
from flightpath.util.os_utility import OsUtility as osut
from flightpath.util.message_utility import MessageUtility as meut
from flightpath.util.json_utility import JsonUtility as jsut
from flightpath.util.state import State
from flightpath.util.editable import EditStates


def run():
    #
    # if --server-mode:
    #    - check for server mode key
    #    - if key found, start a FlightPath Server
    #
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
    # window.showMaximized()
    # window.show()
    sys.exit(app.exec())


class MainWindow(QMainWindow):
    TITLE = "FlightPath • Data Preboarding Development and Operations"

    def __init__(self):
        super().__init__()
        self.reactor = Reactor(self)
        #
        #
        #
        self.setup_ai_flag = False
        noai = State().data.get("llm", {}).get("model", "").strip() == ""
        #
        # if the current project has llm but the env.json doesn't we will still show the
        # splash. this is fine, imho -- the splash isn't completely unexpected.
        #
        guard = GateGuard.show_splash()
        if noai is True or guard is True:
            splashpath = fiut.make_app_path(f"assets{os.sep}images{os.sep}splash.png")
            from flightpath.dialogs.splash_dialog import SplashDialog

            dlg = SplashDialog(
                main=self,
                image_path=splashpath,
                license_url="https://github.com/csvpath/csvpath?tab=LGPL-2.1-1-ov-file#readme",
                copyright_text="© 2025-2026 Atesta Analytics. All rights reserved.",
            )
            dlg.exec()

        #
        # please close will be True if the user chooses not to pick a
        # working directory on first startup. This is not expected to
        # happen, but if it did, we need the application initalization
        # code to not put the app into exec.
        #
        self.main = None
        self._csvpaths = None
        self._csvpath_config = None
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
        self.threadpool = None
        self._selected_file_path = None
        self.last_main = None
        self.build_number = None
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
        # if we fail to / chose not to set a cwd we will close the app. we
        # also use this to make sure we're good to close depending on tabs.
        #
        self.please_close = False
        #
        # at first launch we want to be sure to call show() on child windows
        # after we call show on the main window; otherwise, on Windows, at
        # least, on launch we get a popcorn of windows before things settle
        # down.
        #
        self.launch_shows = []
        #
        # files that are being opened based on clicks could be requested
        # multiple times due to qt internals. this list keeps us from starting
        # two opens on the same file.
        #
        self._is_opening = []
        #
        #
        #
        if not self.state_check():
            return
        # state_check does this
        # self.load_state_and_cd()
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
        self.update_opens()
        #
        # react to light/dark changes
        #
        QCoreApplication.instance().styleHints().colorSchemeChanged.connect(
            self.reactor.on_color_scheme_changed
        )
        if darkdetect.isDark():
            self.on_color_scheme_changed()
        #
        # if the user clicked config AI in the splash
        #
        if self.setup_ai_flag is True:
            self.open_ai_config()
        #
        # kickoff a precache worker to collect some info about files
        #
        QTimer.singleShot(1000, self._run_precacher)
        #
        # prevent double meut asks
        #
        self._asking_save_config = False

    def open_ai_config(self) -> None:
        self.open_config()
        self.config.config_panel.forms_layout.setCurrentIndex(13)
        fallback = f"config{os.sep}about.md"
        self.config.show_help_for_form("llm", fallback=fallback)
        return

    def update_opens(self) -> None:
        data = self.state.data
        i = data.get("opens")
        i = int(i) + 1 if isinstance(i, int) else 1
        data["opens"] = i
        self.state.data = data

    def new_csvpaths(self) -> CsvPaths:
        self._csvpaths = None
        return self.csvpaths

    @property
    def csvpaths(self) -> CsvPaths:
        if self._csvpaths is None:
            c = self.csvpath_config
            if c is None:
                raise ValueError("CsvPaths Config object cannot be None")
            csvpaths = CsvPaths()
            csvpaths.config.configpath = c.configpath
            self._csvpaths = csvpaths
        return self._csvpaths

    def _run_precacher(self) -> None:
        try:
            worker = PreCacheWorker(self.state.cwd, main=self)
            if self.threadpool:
                worker.signals.messages.connect(self.statusBar().showMessage)
                self.threadpool.start(worker, priority=QThread.LowestPriority.value)
        except Exception:
            print(traceback.format_exc())

    def show_now_or_later(self, showable) -> None:
        if not hasattr(showable, "show"):
            raise ValueError(f"Cannot show a {showable}")
        if self.launch_shows is None:
            showable.show()
        else:
            self.launch_shows.append(showable)

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
                # not 100% clear why exit() isn't enough, but it needs a little help.
                # this flag works fine and seems good.
                #
                self.please_close = True
                return False
        self.load_state_and_cd()
        self.statusBar().showMessage(f"  Project changed to: {self.state.cwd}")
        return True

    @property
    def has_csvpath_config(self) -> CsvPathConfig:
        return self._csvpath_config is not None

    @property
    def csvpath_config(self) -> CsvPathConfig:
        if self._csvpath_config is None:
            raise RuntimeError(
                "csvpath config should not be None if we have a selected project and have cded into it"
            )
        return self._csvpath_config

    @csvpath_config.setter
    def csvpath_config(self, config: CsvPathConfig) -> None:
        if config:
            config.project_context = self.state.current_project
        self._csvpath_config = config

    def clear_csvpath_config(self) -> None:
        self._csvpath_config = None
        self._csvpath = None

    @property
    def selected_file_path(self) -> str:
        return self._selected_file_path

    @selected_file_path.setter
    def selected_file_path(self, path: str) -> None:
        self._selected_file_path = path

    def log(self, msg: str) -> None:
        if self.logger is None:
            if self.state.debug == "on":
                self.logger = lout.logger(self.state)
            else:
                self.logger = False
        if self.logger:
            self.logger.debug(msg)

    def load_state_and_cd(self) -> None:
        self.clear_csvpath_config()
        """ sets the project directory into .flightpath file, cds to project dir, and reloads UI. """
        self.state.load_state_and_cd(self)
        #
        # if we have env vars set them for this process
        #
        # self.state.load_env()
        self.startup()

    def startup(self) -> None:
        """(re)loads UI"""
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
        central_widget.setStyleSheet(
            "QSplitter::handle { background-color: #f3f3f3;  margin:1px; }"
        )
        self.setCentralWidget(central_widget)
        self._setup_central_widget()
        #
        # tracks the most recent main_layout index so we can return
        # from config or wherever.
        #
        self.last_main = 0
        self.statusBar().showMessage(f"  Working directory: {self.state.cwd}")

        build_number = fiut.read_string(
            fiut.make_app_path(f"assets{os.sep}build_number.txt")
        ).strip()
        if self.build_number is None:
            self.build_number = QLabel()
            self.build_number.setObjectName("build_number")
            self.build_number.setStyleSheet("QLabel {font-size:10px;color:#999}")
            self.statusBar().addPermanentWidget(self.build_number, 0)
        self.build_number.setText(build_number)
        md = HelpFinder(main=self.main).help("welcome/welcome.md")
        self.helper.get_help_tab().setMarkdown(md)

    def _setup_central_widget(self) -> None:
        """central widget is a vert splitter with left & right
        sidebars and a main area in the middle of top data
        and bottom help and feedback."""
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
        self.main.setSizes([5, 1])
        self.helper.assure_help_tab()
        #
        # make the AI tab ahead of so it is present for darkdetect
        #
        self.ai_query_tab = QueryTabWidget(main=self)
        #
        # left side tree
        #
        self.sidebar = Sidebar(main=self)
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
        # add columns to splitter
        #
        cw.addWidget(self.sidebar)
        cw.addWidget(self.main)
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

        self.sidebar_rt_top = SidebarNamedFiles(
            main=self, config=self.csvpath_config, role=1
        )
        self.rt_col.addWidget(self.sidebar_rt_top)

        self.sidebar_rt_mid = SidebarNamedPaths(
            main=self, config=self.csvpath_config, role=2
        )
        self.rt_col.addWidget(self.sidebar_rt_mid)

        self.sidebar_rt_bottom = SidebarArchive(
            main=self, config=self.csvpath_config, role=3
        )
        self.rt_col.addWidget(self.sidebar_rt_bottom)
        #
        # add tabs to tab widget
        #
        self.rt_tab_widget.addTab(self.rt_col, "Ops")
        self.rt_tab_widget.addTab(self.ai_query_tab, "AI")
        self.rt_tab_widget.addTab(self.rt_col_helpers, "Help")
        #
        # functions and docs setup below in the tab displaying logic.
        #
        #
        # set size policies. this explicitness may not be strictly necessary.
        #
        self.rt_tab_box.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.rt_tab_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.rt_tab_box.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.rt_col_helpers.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.rt_col.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.sidebar_rt_top.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.sidebar_rt_mid.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.sidebar_rt_bottom.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        #
        # hide the tabs if the main_layout is pointed at Welcome or Config
        #
        self.hide_rt_tabs()
        #
        # set the default relative sizes
        #
        cw.setSizes([100, 1400, 100])
        #
        #
        #
        self.reactor.do_connects()

    def renew_sidebar_archive(self) -> None:
        #
        # we can just reset, rather than recreating. doesn't solve for
        # adding the new items w/o changing the layout, but at least it
        # is lighter weight and more pointer/thread friendly.
        #
        d = self.sidebar_rt_bottom
        self.sidebar_rt_bottom = SidebarArchive(
            main=self, config=self.csvpath_config, role=3, tabs=d.tabs
        )
        self.rt_col.replaceWidget(2, self.sidebar_rt_bottom)
        d.deleteLater()

    def renew_sidebar_named_files(self) -> None:
        #
        # we can just reset, rather than recreating. doesn't solve for
        # adding the new items w/o changing the layout, but at least it
        # is lighter weight and more pointer/thread friendly.
        #
        d = self.sidebar_rt_top
        self.sidebar_rt_top = SidebarNamedFiles(
            main=self, config=self.csvpath_config, role=3
        )
        self.rt_col.replaceWidget(0, self.sidebar_rt_top)
        d.deleteLater()

    def renew_sidebar_named_paths(self) -> None:
        #
        # we can just reset, rather than recreating. doesn't solve for
        # adding the new items w/o changing the layout, but at least it
        # is lighter weight and more pointer/thread friendly.
        #
        d = self.sidebar_rt_mid
        self.sidebar_rt_mid = SidebarNamedPaths(
            main=self, config=self.csvpath_config, role=3
        )
        self.rt_col.replaceWidget(1, self.sidebar_rt_mid)
        d.deleteLater()

    def hide_rt_tabs(self) -> None:
        i = self.main_layout.currentIndex()
        if i in [0, 2]:
            self.rt_tab_widget.tabBar().hide()

    @property
    def helper(self) -> QTextEdit:
        if self._helper is None:
            self._helper = Helper(main=self)
        return self._helper

    def setup_named_files(self) -> None:
        self.sidebar_rt_top = SidebarNamedFiles(
            main=self, config=self.csvpath_config, role=1
        )
        self.grid_layout.addWidget(self.sidebar_rt_top, 0, 2, 1, 1)

    def setup_named_paths(self) -> None:
        self.sidebar_rt_mid = SidebarNamedPaths(
            main=self, config=self.csvpath_config, role=2
        )
        self.grid_layout.addWidget(self.sidebar_rt_mid, 1, 2, 1, 1)

    def setup_archive(self) -> None:
        self.sidebar_rt_bottom = SidebarArchive(
            main=self, config=self.csvpath_config, role=3
        )
        self.grid_layout.addWidget(self.sidebar_rt_bottom, 2, 2, 1, 1)

    def show_welcome_screen(self):
        self.sidebar.file_navigator.selectionModel().clear()
        self.last_main = self.main_layout.currentIndex()
        self.main_layout.setCurrentIndex(0)
        self.statusBar().showMessage(self.state.cwd)

    @property
    def current_doc_tab(self) -> QWidget:
        di = self.content.tab_widget.currentIndex()
        if di is not None and di > -1:
            return self.content.tab_widget.widget(di)
        return None

    def rt_tabs_hide(self) -> None:
        self.rt_tab_widget.tabBar().setCurrentIndex(0)
        self.rt_tab_widget.tabBar().hide()

    def rt_tabs_show(self) -> None:
        self.show_now_or_later(self.rt_tab_widget.tabBar())
        self.ai_query_tab.form.use_doc_checkbox.setChecked(False)
        self.ai_query_tab.form.on_use_doc(Qt.CheckState.Unchecked)

    @Slot(tuple)
    def update_json_views(self, worker_data):
        try:
            filepath, data, editable = worker_data  # pylint: disable=W0612
            if isinstance(data, Exception):
                meut.message2(
                    parent=self,
                    icon=QMessageBox.Critical,
                    title="File opening error",
                    msg=f"Error: {data}",
                    callback=self._clear_is_opening,
                    args={"path": filepath},
                )
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
                if (
                    filepath.endswith("manifest.json")
                    and EditStates.UNEDITABLE == editable
                ):
                    json_view = JsonViewer(
                        main=self, parent=self.content.tab_widget, editable=editable
                    )
                    data = json.dumps(data, indent=2)
                    json_view.open_file(path=filepath, data=data)
                    json_view.setObjectName(filepath)
                    self.content.tab_widget.addTab(
                        json_view, os.path.basename(filepath)
                    )
                else:
                    json_view = JsonViewer2(self, editable)
                    json_view.open_file(path=filepath, data=data)
                    json_view.setObjectName(filepath)
                    self.content.tab_widget.addTab(
                        json_view, os.path.basename(filepath)
                    )
            else:
                json_view = json_view[1]
            taut.select_tab(self.content.tab_widget, json_view)
            self.rt_tabs_show()
        except Exception:
            print(traceback.format_exc())
        finally:
            self._clear_is_opening(path=filepath)

    @Slot(tuple)
    def update_md_views(self, worker_data):
        filepath, data, editable = worker_data  # pylint: disable=W0612
        try:
            if isinstance(data, Exception):
                meut.warning2(
                    parent=self,
                    title="File opening error",
                    msg=f"Error: {data}",
                    callback=self._clear_is_opening,
                    args={"path": filepath},
                )
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
                # the displaying:bool argument determines if it is an .md or .txt file.
                # odd, but workable. it doesn't affect the editability of the file.
                #
                displaying = True
                #
                # being over careful because this is just a fix, not new work
                #
                try:
                    _, ext = os.path.splitext(filepath)
                    if ext in ["log", "txt"]:
                        displaying = False
                except Exception:
                    print(traceback.format_exc())
                    ...
                view = MdViewer(main=self, editable=editable, displaying=displaying)
                view.setObjectName(filepath)
                #
                # TODO: oddly, we use the worker to open and then just open again
                # this is a legacy of something validation related. it exists
                # in csvpath and json files too.
                #
                view.open_file(path=filepath, data=data)
                self.content.tab_widget.addTab(view, os.path.basename(filepath))
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
            self.rt_tabs_show()
        finally:
            self._clear_is_opening(path=filepath)

    @Slot(tuple)
    def update_csvpath_views(self, worker_data):
        filepath, data, editable = worker_data  # pylint: disable=W0612
        if isinstance(data, Exception):
            meut.warning2(
                parent=self,
                title="File opening error",
                msg=f"Error: {data}",
                callback=self._clear_is_opening,
                args={"path": filepath},
            )
            return
        try:
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
                self.content.tab_widget.addTab(csvpath_view, os.path.basename(filepath))

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
            self.rt_tabs_show()
        finally:
            self._clear_is_opening(path=filepath)

    @Slot(tuple)
    def update_data_views(self, worker_data):
        msg, lines, filepath, data, lines_to_take, editable, largefile = worker_data  # pylint: disable=W0612
        if isinstance(lines, Exception):
            meut.warning2(
                parent=self,
                title="File opening error",
                msg=f"Error: {lines}",
                callback=self._clear_is_opening,
                args={"path": filepath},
            )
            return
        #
        #
        #
        if largefile is True:
            meut.warning2(
                parent=self,
                title="Large file warning",
                msg="FlightPath is optimized for samples, not large files. Only 66,000 lines loaded.",
                callback=self._do_update_data_views,
                args={"worker_data": worker_data},
            )
            return
        self._do_update_data_views(worker_data=worker_data)

    def _do_update_data_views(self, *, worker_data) -> None:
        msg, lines, filepath, data, lines_to_take, editable, largefile = worker_data  # pylint: disable=W0612
        table_model = TableModel(data=data, editable=(editable == EditStates.EDITABLE))
        self.last_main = self.main_layout.currentIndex()
        self.main_layout.setCurrentIndex(1)
        #
        # need to add a tab
        #   need to check if a tab already exists?
        #
        obj_name = filepath
        data_view = taut.find_tab(self.content.tab_widget, filepath)
        dv = None
        #
        # hang to the tuple for a min. in case we have a json viewer
        #
        if data_view is None:
            #
            # content is not actually the parent. the tabs are the parent.
            #
            dv = DataViewer(
                main=self, parent=self.content.tab_widget, editable=editable
            )
            dv.setObjectName(obj_name)
            #
            # make sure we have the lines so the raw_viewer can take the same
            #
            dv.lines_to_take = lines_to_take
            name = os.path.basename(filepath)
            self.content.tab_widget.addTab(dv, name)
        else:
            #
            # if we have a jsonviewer2 it is because we opened using right-click edit as json.
            # then we clicked the file name in a regular way. ideally the jsonviewer2 should be
            # replaced by a dataviewer.
            #
            if isinstance(data_view[1], JsonViewer2):
                #
                # close the json view. it will prompt to save. we should be Ok with getting
                # prompted i think.
                #
                #
                # remove old view
                #
                self.content.tab_widget.close_tab(filepath)
                #
                # create the new view
                #
                dv = DataViewer(
                    main=self, parent=self.content.tab_widget, editable=editable
                )
                dv.setObjectName(obj_name)
            else:
                #
                # find_tab -> (index, widget)
                #
                dv = data_view[1]
        try:
            #
            # make sure we have the lines so the raw_viewer can take the same
            #
            dv.lines_to_take = lines_to_take
            name = os.path.basename(filepath)
            self.content.tab_widget.addTab(dv, name)
            table_model.signals.edit_made.connect(dv.on_edit_made)
            table_model.signals.columns_inserted.connect(dv.on_row_or_column_edit)
            table_model.signals.columns_deleted.connect(dv.on_row_or_column_edit)
            table_model.signals.rows_inserted.connect(dv.on_row_or_column_edit)
            table_model.signals.rows_deleted.connect(dv.on_row_or_column_edit)
            dv.display_data(table_model)
            #
            # when  data _view is visible we show the sample tool bar
            #
            if jsut.is_jsonl(filepath):
                self.content.toolbar.enable()
            else:
                self.content.toolbar.enable()
            self.show_now_or_later(self.content.toolbar)
            taut.select_tab(self.content.tab_widget, dv)
            self.rt_tabs_show()
        except Exception:
            print(traceback.format_exc())
        finally:
            self._clear_is_opening(path=filepath)

    def _clear_is_opening(self, *, path: str) -> None:
        if path in self._is_opening:
            self._is_opening.remove(path)

    def is_doc_editable(self, path) -> str:
        return fiut.is_doc_editable(self, path)

    def read_validate_and_display_file(
        self, editable=EditStates.EDITABLE, *, finished_callback=None
    ) -> QRunnable:
        return self.read_validate_and_display_file_for_path(
            self.selected_file_path,
            editable=editable,
            finished_callback=finished_callback,
        )

    def read_validate_and_display_file_for_path(
        self, path: str, editable=EditStates.EDITABLE, *, finished_callback=None
    ) -> QRunnable:
        if path in self._is_opening:
            return
        self._is_opening.append(path)
        #
        # callbacks passed into this method should be watched closely. the find data by ref dialog
        # had trouble getting them to behave correctly.
        #
        info = QFileInfo(path)
        worker = None
        nos = Nos(path)
        isfile = nos.isfile()
        if isfile and info.suffix() in self.csvpath_config.get(
            section="extensions", name="csv_files"
        ):  # pylint: disable=E1135
            worker = GeneralDataWorker(
                path,
                self,
                rows=self.content.toolbar.rows.currentText(),
                sampling=self.content.toolbar.sampling.currentText(),
                delimiter=self.content.toolbar.delimiter_char(),
                quotechar=self.content.toolbar.quotechar_char(),
                editable=editable,
            )
            worker.signals.finished.connect(self.update_data_views)
            if finished_callback is not None:
                worker.signals.finished.connect(finished_callback)
            worker.signals.messages.connect(self.statusBar().showMessage)
            self.threadpool.start(worker)
        elif isfile and info.suffix() in self.csvpath_config.get(
            section="extensions", name="csvpath_files"
        ):  # pylint: disable=E1135
            worker = CsvpathFileWorker(path, self, editable=editable)
            worker.signals.finished.connect(self.update_csvpath_views)
            if finished_callback is not None:
                worker.signals.finished.connect(finished_callback)
            worker.signals.messages.connect(self.statusBar().showMessage)
            self.threadpool.start(worker)
        elif isfile and info.suffix() == "json":
            self.spin_up_json_worker(
                path=path, editable=editable, finished_callback=finished_callback
            )
        elif isfile and info.suffix() in ["md", "html", "txt", "log"]:
            self.spin_up_md_worker(
                path=path, editable=editable, finished_callback=finished_callback
            )
        elif not info.isFile():
            meut.message2(
                parent=self, title="File opening error", msg=f"Cannot open {path}"
            )
            return
        else:
            meut.warning2(
                parent=self,
                msg=f"Unknown file type {info.suffix()}",
                title="Cannot Open",
                callback=self.clear_views,
                args={"filepath": path},
            )
            return
        return worker

    def spin_up_md_worker(self, *, path, editable, finished_callback=None) -> QRunnable:
        worker = MdWorker(path, self, editable=editable)
        worker.signals.finished.connect(self.update_md_views)
        if finished_callback is not None:
            worker.signals.finished.connect(finished_callback)
        worker.signals.messages.connect(self.statusBar().showMessage)
        self.threadpool.start(worker)
        return worker

    def spin_up_json_worker(
        self, *, path, editable, finished_callback=None
    ) -> QRunnable:
        worker = JsonDataWorker(path, self, editable=editable)
        if finished_callback is not None:
            worker.signals.finished.connect(finished_callback)
        worker.signals.finished.connect(self.update_json_views)
        worker.signals.messages.connect(self.statusBar().showMessage)
        self.threadpool.start(worker)
        return worker

    def run_paths(
        self, *, method: str, named_paths_name: str, named_file_name: str, template: str
    ) -> None:
        csvpaths = self.new_csvpaths()
        runner = RunWorker(
            method=method,
            named_paths_name=named_paths_name,
            named_file_name=named_file_name,
            template=template,
            csvpaths=csvpaths,
        )
        #
        #
        #
        params = {
            "named_paths_name": named_paths_name,
            "run_dir": "",
            "worker": id(runner),
            "named_file_name": named_file_name,
            "template": template,
            "method": method,
            "cid": str(id(csvpaths)),
            "csvpaths": csvpaths,
        }
        self.sidebar_rt_bottom.on_query_submitted(params)
        #
        # clear any existing logs to .bak. we have to shutdown to be sure that the
        # file is released. that's not a problem because it is CsvPath logging, not
        # FlightPath logging.
        #
        lout.rotate_log(self.state.cwd, self.csvpath_config)
        #
        #
        #
        runner.signals.started.connect(self.sidebar_rt_bottom.on_run_started)
        runner.signals.finished.connect(self._display_log)
        runner.signals.error.connect(self._display_error)
        runner.signals.messages.connect(self.statusBar().showMessage)
        self.threadpool.start(runner)

    @Slot(tuple)
    def _display_error(self, t: tuple[str]) -> None:
        #
        # need a more specific way to handle errors
        #
        meut.message2(
            parent=self,
            msg=t[0],
            title="Error in run",
            callback=self._display_log,
            args={"t": t, "error": True},
        )

    @Slot(tuple)
    def _display_log(self, t: tuple[str], *, error=False) -> None:
        #
        # first let the archive know if the item is green or red
        #
        cid = str(id(t[1]))
        if t and len(t) >= 2:
            self.sidebar_rt_bottom.run_ended(cid, error)

        log = QWidget(self.helper.help_and_feedback)
        log.setObjectName(f"Log-{cid}")
        self.helper.help_and_feedback.addTab(log, "Log")
        #
        # the logs tab should be the first showing, at least unless/until
        # we add more run results tabs.
        #
        i = self.helper.help_and_feedback.count()
        self.helper.help_and_feedback.setCurrentIndex(i - 1)

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
        # self.sidebar_rt_bottom.update_run_item_status(cid, "error" if error is True else "done")
        self.renew_sidebar_archive()

    def clear_views(self):
        self.content.close_all_tabs()

    def is_writable(self, path) -> bool:
        return fiut.is_writable_dir(path)

    def save_sample(self, *, path: str, name: str, data: str) -> str:
        parts = pathu.parts(name)
        name = parts[len(parts) - 1]
        path = self.sidebar.selected_file_path()
        if path and Nos(path).isfile:
            bpath = os.path.dirname(path)
            if bpath == path or path == name:
                path = ""
            else:
                path = bpath
        if path in [None, ""]:
            path = self.state.cwd
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
        dialog.setLabelText("Enter a name for the file:")
        dialog.setTextValue(name)
        ok = dialog.exec()
        new_name = dialog.textValue()
        #
        #
        #
        if ok and new_name and new_name.strip() != "":
            exts = [
                "csv",
                "json",
                "jsonl",
                "jsonlines",
                "ndjson",
                "xlsx",
                "xls",
                "parquet",
                "md",
                "txt",
                "log",
            ]
            if isinstance(data, str) and not fiut.is_a(new_name, exts):
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
            if isinstance(data, str):
                with open(path, "w") as file:
                    file.write(data)
            else:
                with DataFileWriter(path=path) as file:  # pylint: disable=E0110
                    writer = csv.writer(file.sink)
                    writer.writerows(data)
            return path
        else:
            return None

    # ================== config stuff ====================

    def _has_config_changes(self) -> bool:
        ret = (
            self.config
            and self.config.ready is True
            and self.config.toolbar._button_save.isEnabled()
        )
        # print(f"_has_config_changes: ret: {ret}")
        # from csvpath.util.log_utility import LogUtility as lout
        # lout.log_brief_trace()
        return ret

    def question_save_config_if(self, *, callback: Callable = None) -> None:
        if self._asking_save_config is True:
            return
        if self._has_config_changes():
            # print(f"question_save_config_if: doing meut")
            self._asking_save_config = True
            meut.yesNo2(
                parent=self,
                callback=self._answer_save_config,
                title="Config changed",
                msg="Save config changes?",
                args={"callback": callback},
            )
        elif callback:
            # print(f"question_save_config_if: no changes, calling back {callback}")
            callback()
        else:
            ...

    @Slot(int)
    def _answer_save_config(self, answer, *, callback: Callable = None) -> None:
        # print(f"_answer_save_config: answer: {answer}")
        if answer == QMessageBox.Yes:
            self.save_config_changes()
        self.reset_config_toolbar()
        self._asking_save_config = False
        if callback:
            # print(f"_answer_save_config: calling back {callback}")
            callback()

    def open_config(self):
        if self.main_layout.currentIndex() != 2:
            self.last_main = self.main_layout.currentIndex()
            self.main_layout.setCurrentIndex(2)
            self.cancel_config_changes()
            self.config.show_help()
            #
            # we should make the currently showing form selected and
            # when the current form is BlankForm we should deselect all;
            # for first release we're letting it ride.
            #

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
        self.csvpath_config.reload()
        self.config.config_panel.populate_all_forms()
        self.reset_config_toolbar()

    def save_config_changes(self):
        try:
            self.config.config_panel.save_all_forms()
            self.config.config_panel.populate_all_forms()
            self.reset_config_toolbar()
        except Exception as e:
            meut.message2(
                parent=self,
                title="Error saving config",
                msg=f"Error saving config: {e}",
            )

    # ================== app closing stuff ====================

    def closeEvent(self, event):
        if self.please_close is True:
            # print(f"closeEvent: pls close: accepting")
            event.accept()
            return
        if (
            not hasattr(self, "sidebar")
            and not hasattr(self, "main_layout")
            and not hasattr(self, "content")
            and not self._has_config_changes()
        ):
            # print(f"xx: nothing setup: accepting")
            event.accept()
            return
        #
        # it is important to check config first. if we clear tabs first while looking at
        # config we get a change view event that checks config but without having the
        # finish_closing_if callback
        #
        # also note that we are triggering both config change check and tabs close check
        # in one pass. before we were using two independent passes, but that doesn't
        # improve anything. in principle the last config check in finish_closing_if should
        # not be needed because of this change, but it doesn't hurt to check again.
        #
        accept = True
        if self._has_config_changes():
            # print(f"xx: ignoring because has config changes: {self._has_config_changes()}")
            self.question_save_config_if(callback=self.finish_closing_if)
            event.ignore()
            accept = False
        unsaved = not self.content.all_files_are_saved()
        if unsaved is True:
            # print(f"closeEvent: ignoring because unsaved: {unsaved}")
            self.content.close_all_tabs(callback=self.finish_closing_if)
            event.ignore()
            accept = False
        if accept is True:
            # print(f"closeEvent: accepting because no reason not to")
            event.accept()

    def finish_closing_if(self) -> None:
        if (
            self.content
            and self.content.tab_widget
            and self.content.tab_widget.count() > 0
        ):
            ...
            # print("finish closing if: not ready to close because tabs")
        elif self._has_config_changes():
            # print("finish closing if: not ready to close because there are cofig changes")
            self.question_save_config_if(callback=self.finish_closing_if)
        else:
            # print("finish closing if: ready to close. setting please_close = True")
            self.please_close = True
            QApplication.quit()


if __name__ == "__main__":
    run()
