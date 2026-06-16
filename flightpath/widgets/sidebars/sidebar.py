import os
import traceback

from PySide6.QtWidgets import (
    QPushButton,
    QWidget,
    QComboBox,
    QVBoxLayout,
    QSizePolicy,
)

from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtWidgets import QFileSystemModel

from csvpath.util.nos import Nos

from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.widgets.clickable_label import ClickableLabel
from flightpath.widgets.custom_tree_view import CustomTreeView
from flightpath.widgets.sidebars.sidebar_named_paths import SidebarNamedPaths
from flightpath.widgets.sidebars.sidebar_named_files import SidebarNamedFiles
from flightpath.widgets.file_tree_model.directory_filter_proxy_model import (
    DirectoryFilterProxyModel,
)
from flightpath.widgets.sidebars.sidebar_actions import SidebarActions
from flightpath.widgets.sidebars.sidebar_context_menu import SidebarContextMenuMaker
from flightpath.util.help_finder import HelpFinder
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.message_utility import MessageUtility as meut
from flightpath.util.string_utility import StringUtility as strut


class Sidebar(QWidget):
    NEW_PROJECT = "Create new project"

    def __init__(self, main, role=0):
        super().__init__()
        self.main = main
        self.file_navigator = None
        #
        # cutted holds any cut-n-paste source path
        #
        self.cutted = None
        self.copied = None
        self.actions = SidebarActions(main=self.main, parent=self)

        #
        # we use the thread pool to run precache workers
        #
        self.threadpool = None
        self.setMinimumWidth(300)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setSpacing(0)
        layout.setContentsMargins(4, 3, 1, 3)
        self.icon_label = ClickableLabel()
        pixmap = QPixmap(fiut.make_app_path(f"assets{os.sep}logo-173x40.png"))
        self.icon_label.setPixmap(pixmap)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.icon_label)
        self.icon_label.setStyleSheet(
            "background-color: #ffffff;border:1px solid #c9c9c9;"
        )

        self.projects = QComboBox()
        size = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.projects.setSizePolicy(size)

        self.projects.activated.connect(self.actions._on_project_changed)
        self.projects.setStyleSheet(
            "QComboBox { margin:1px; height:23px; padding-left:5px;}"
        )
        #
        #
        #
        box = HelpIconPackager.add_help(
            main=self.main, widget=self.projects, on_help=self.on_click_cwd_help
        )
        layout.addWidget(box)
        #
        #
        #
        self._set_project_from_state()
        self.open_config_box = self._help_button(
            text="Open config",
            on_click=self.main.open_config,
            on_help=self.on_click_open_config_help,
        )
        layout.addWidget(self.open_config_box)
        #
        # holds the last file right-clicked or None for the root whitespace or no previous rt-clicks
        #
        self._last_path = None
        self._last_file_index = None

        self.stage_dialog = None
        self.load_dialog = None

    def new_project_name(self, callback) -> None:
        def ask():
            meut.input2(
                parent=self,
                title=self.NEW_PROJECT,
                msg="Enter the new project's name",
                callback=handle_answer,
            )

        def handle_answer(t: tuple[str, bool]):
            name, ok = t
            if not ok:
                callback(None)
                return
            if not strut.good_name(name):
                meut.warning2(
                    parent=self,
                    title="Bad name",
                    msg="Project names can only have alpha-numeric characters, spaces, dashes, and underscores",
                    callback=ask,
                )
                return
            name = name.strip()
            if name in self._project_names():
                meut.warning2(
                    parent=self,
                    title="Bad name",
                    msg=f"A {name} project already exists",
                    callback=ask,
                )
                return
            callback(name)

        ask()

    def _set_project_from_state(self) -> None:
        #
        # recreate all UI parts
        #
        self._setup_tree(replace=True)
        self._build_combo()
        #
        # sometimes it gets confused about the l&f
        #
        self.main.reactor.on_color_scheme_changed()

    def _build_combo(self) -> None:
        self.projects.clear()
        proj = self.main.state.current_project
        ps = self._project_names()
        for p in ps:
            self.projects.addItem(p)
            if p == proj:
                self.projects.setCurrentText(p)
        self.projects.insertSeparator(self.projects.count())
        self.projects.addItem(Sidebar.NEW_PROJECT)

    def _project_names(self) -> list[str]:
        projs = os.path.join(self.main.state.home, self.main.state.projects_home)
        nos = Nos(projs)
        lst = nos.listdir(dirs_only=True)
        #
        # should not have to filter dirs because dirs_only=True, but stupidly the files
        # version of Nos only filters for files. to-be-fixed soon!
        #
        # csvpath has a clear test: /Users/davidkershaw/dev/csvpath/tests/dirs/test_dirs_local.py
        #
        # ps = [p for p in lst if not Nos(os.path.join(projs, p)).isfile()]
        #
        ps = lst
        ps.sort()
        return ps

    @property
    def last_file_index(self) -> QModelIndex:
        return self._last_file_index

    @last_file_index.setter
    def last_file_index(self, i: QModelIndex) -> None:
        self._last_file_index = i

    def _help_button(self, *, text: str, on_click, on_help) -> QWidget:
        button = QPushButton()
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setStyleSheet("QPushButton { margin-top:1px; height:23px; }")
        box = HelpIconPackager.add_help(main=self.main, widget=button, on_help=on_help)
        button.setText(text)
        button.clicked.connect(on_click)
        return box

    def on_click_cwd_help(self) -> None:
        md = HelpFinder(main=self.main).help("sidebar/cwd.md")
        self.main.helper.get_help_tab().setMarkdown(md)
        if not self.main.helper.is_showing_help():
            self.main.helper.on_click_help()

    def on_click_open_config_help(self) -> None:
        md = HelpFinder(main=self.main).help("sidebar/open_config.md")
        self.main.helper.get_help_tab().setMarkdown(md)
        if not self.main.helper.is_showing_help():
            self.main.helper.on_click_help()

    def _setup_tree(self, *, replace=False) -> None:
        old = self.file_navigator
        self.file_navigator = CustomTreeView()
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(self.main.state.cwd)

        pathses = self.main.csvpath_config.get(
            section="extensions", name="csvpath_files"
        )
        fileses = self.main.csvpath_config.get(section="extensions", name="csv_files")
        pathses = pathses if isinstance(pathses, list) else [pathses]
        fileses = fileses if isinstance(fileses, list) else [fileses]
        exts = fileses + pathses

        exts = [f"*.{e}" for e in exts]
        #
        # we need json, of course. no reason to think it would be in csvpaths or csv extensions, but
        # checking just in case.
        #
        if "*.json" not in exts:
            exts.append("*.json")
        #
        # added for md/other user created docs. html is not a thing atm, but it could be coming.
        #
        if "*.html" not in exts:
            exts.append("*.html")
        if "*.md" not in exts:
            exts.append("*.md")
        if "*.txt" not in exts:
            exts.append("*.txt")
        if "*.log" not in exts:
            exts.append("*.log")
        #
        # TODO: find the current key dirs in config and filter out
        #
        self.file_model.setNameFilters(exts)
        self.file_model.setNameFilterDisables(False)
        #
        # exp. don't show the std background dirs
        #
        self.proxy_model = DirectoryFilterProxyModel(
            excluded_dirs=["config", "logs", "cache", "archive", "inputs", "logs_bak"],
            sidebar=self,
        )
        self.proxy_model.setSourceModel(self.file_model)
        self.proxy_model.sort(0, Qt.AscendingOrder)
        self.file_navigator.setModel(self.proxy_model)
        self.file_navigator.setRootIndex(
            self.proxy_model.mapFromSource(self.file_model.index(self.main.state.cwd))
        )
        #
        # this is alpha-sort descending. :/
        #
        self.file_navigator.setSortingEnabled(True)

        self._show_only_name_column_in_file_navigator(
            self.file_model, self.file_navigator
        )
        self.file_navigator.setHeaderHidden(True)
        #
        #
        #
        self.context_menu_maker = SidebarContextMenuMaker(main=self.main, parent=self)
        self.file_navigator.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_navigator.customContextMenuRequested.connect(self._show_context_menu)
        #
        # reconnect the nav so we react to clicking on files
        #
        self.file_navigator.clicked.connect(self.main.reactor.on_tree_click)

        if replace and old:
            self.layout().replaceWidget(old, self.file_navigator)
        else:
            self.layout().addWidget(self.file_navigator)

    def _has_llm(self) -> bool:
        m = self.main.csvpath_config.get(section="llm", name="model")
        if m is None:
            return False
        if str(m).strip() == "":
            return False
        m = self.main.csvpath_config.get(section="llm", name="api_base")
        return True

    def _show_context_menu(self, position):
        self.context_menu_maker.show_context_menu(position)

    def _worksheets_for_path(self, path: str) -> list[str]:
        if path is None:
            raise ValueError("Path cannot be None")
        import pylightxl as xl

        db = xl.readxl(fn=path)
        names = db.ws_names
        if names is None:
            return []
        return names

    @property
    def current_path(self) -> str:
        index = self.file_navigator.currentIndex()
        if index.isValid():
            path = self.proxy_model.filePath(index)
            return path
        return None

    @property
    def current_path_is_dir(self) -> str:
        nos = Nos(self.current_path)
        return nos.exists() and not nos.isfile()

    def _renew_sidebars(self) -> None:
        #
        # TODO: we recreate all the trees. not great due to slow refresh from remote.
        # but for now it should work. refreshing named_files is probably fair, but that's
        # also tricky because we'd want to recreate the opened/closed state of the folders
        # and if we did that the refresh might slow down potentially a lot. so long-term,
        # seems like we should capture what is registered and manually add it. no fun. :/
        #
        # we're only actually doing named_paths here. what's up with that?
        #
        self.main.sidebar_rt_mid = SidebarNamedPaths(
            main=self.main, config=self.main.csvpath_config, role=2
        )
        self.main.rt_col.replaceWidget(1, self.main.sidebar_rt_mid)
        # self.main.sidebar_rt_mid.view.clicked.connect(self.main.on_named_paths_tree_click)

    def do_stage(self) -> None:
        #
        # collect the vars needed
        #
        template = self.stage_dialog.template_ctl.text()
        template = template.strip() if template else None
        if template == "":
            template = None
        if template and not template.endswith(":filename"):
            """
            meut.warning2(
                parent=self,
                msg="The :filename token must be the last component of the template",
                title="Incomplete",
            )
            """
            self.stage_dialog.warning(
                msg="The :filename token must be the last component of the template",
                title="Incomplete",
            )
            return

        regex = None
        if hasattr(self.stage_dialog, "regex"):
            regex = self.stage_dialog.regex_ctl.text()
        named_file_name = self.stage_dialog.named_file_name_ctl.text()
        named_file_name = named_file_name.strip() if named_file_name else ""

        recurse = self.stage_dialog.recurse_ctl.isChecked()
        name = self.stage_dialog.path
        paths = self.main.csvpaths
        #
        # have to override the filesystem prohibit because it doesn't make sense
        # here. we are all local file-based atm and also control config.
        #
        paths.config.set(section="inputs", name="allow_local_files", value=True)
        #
        # got all the vars
        #
        nos = Nos(name)
        try:
            if nos.isfile():
                paths.file_manager.add_named_file(
                    name=named_file_name, path=name, template=template
                )
            else:
                if self.stage_dialog.separate_ctl.isChecked():
                    paths.file_manager.add_named_files_from_dir(
                        name=None,
                        dirname=name,
                        template=template,
                        recurse=recurse,
                        regex=regex,
                    )
                else:
                    if not named_file_name or named_file_name.strip() == "":
                        """
                        meut.warning2(
                            parent=self,
                            title="No name given",
                            msg="You must provide a named-file name",
                        )
                        """
                        self.stage_dialog.warning(
                            title="No name given",
                            msg="You must provide a named-file name",
                        )
                        return
                    paths.file_manager.add_named_files_from_dir(
                        name=named_file_name,
                        dirname=name,
                        template=template,
                        recurse=recurse,
                    )
            if self.stage_dialog.default_ctl.isChecked():
                paths.file_manager.describer.store_template(
                    named_file_name, "" if template is None else template
                )
        except Exception as e:
            #
            # changed the meut to have self as parent, not the dialog. if
            # that doesn't work on windows try closing and noneifing the
            # dialog first. <<< it didn't work. but having the dialog use
            # meut to open the dialog works great.
            #
            # test with templates like:
            #    :0/test/:1test:filename
            #    o\:1/test\c:\\
            #
            print(traceback.format_exc())
            self.stage_dialog.warning(title="Stage error", msg=f"{e}")
            return
        #
        # TODO: we recreate all the trees. very bad idea due to slow refresh from remote.
        # but for now it should work. refreshing named_files is probably fair, but that's
        # also tricky because we'd want to recreate the opened/closed state of the folders
        # and if we did that the refresh might slow down potentially a lot. so long-term,
        # seems like we should capture what is registered and manually add it. no fun. :/
        #
        self.main.sidebar_rt_top = SidebarNamedFiles(
            main=self.main, config=self.main.csvpath_config, role=1
        )
        self.main.rt_col.replaceWidget(0, self.main.sidebar_rt_top)
        # self.main.sidebar_rt_top.view.clicked.connect(self.main.on_named_file_tree_click)
        #
        #
        #
        self.stage_dialog.close()
        #
        # TODO: add delete later?
        #
        self.stage_dialog.deleteLater()
        self.stage_dialog = None
        self.main.welcome.update_run_button()
        self.main.welcome.update_find_data_button()

    def _valid_new_folder(self, name: str) -> tuple[bool, str]:
        b = name.find(".") == -1
        if b:
            return b, "Ok"
        return b, "Failed"

    def _valid_new_file(self, name: str) -> tuple[bool, str]:
        if name is None or name.strip() == "":
            return False, "Name cannot be empty"
        if (name.find("/") > -1 or name.find("\\") > -1) and not (
            name.startswith(self.main.state.cwd) or name.startswith(f".{os.sep}")
        ):
            return False, "File must be in or below the working directory"
        if name.find(".", 1) == -1:
            return (
                False,
                "File extension not recognized. See Config > Extensions settings.",
            )
        ext = name[name.rfind(".") + 1 :]
        if ext == "json":
            return True, "Ok"
        #
        # do we want to allow creating html files?  that's a whole can of worms.
        # maybe just display them. perhaps also editing, to a degree?
        #
        if ext in ["md", "txt"]:
            return True, "Ok"
        if ext not in self.main.csvpath_config.get(
            section="extensions", name="csvpath_files"
        ) and ext not in self.main.csvpath_config.get(
            section="extensions", name="csv_files"
        ):
            return False, "Extension must be for csvpaths, data, text, or markdown"
        #
        # all data files are editable now, except xlsx/xls
        #
        # if ext in self.main.csvpath_config.get(section="extensions", name="csv_files"):
        #    meut.message( title="Data file", msg="You are creating an empty data file that must be edited outside of FlightPath" )
        if ext in ["xlsx", "xsl"]:
            return False, "Excel files are not supported in FlightPath at this time"

        return True, "Ok"

    def selected_file_path(self) -> str:
        index = self.file_navigator.currentIndex()
        if index.isValid():
            path = self.proxy_model.filePath(index)
            return path
        return None

    def _show_only_name_column_in_file_navigator(self, file_model, file_navigator):
        for column in range(file_model.columnCount()):
            if column != 0:  # 0 is the name column
                file_navigator.setColumnHidden(column, True)
