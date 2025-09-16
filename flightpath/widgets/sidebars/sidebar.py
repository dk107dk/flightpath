import sys
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QPushButton,
    QWidget,
    QComboBox,
    QMenu,
    QMessageBox,
    QInputDialog,
    QVBoxLayout,
    QSizePolicy
)

from PySide6.QtGui import QPixmap, QIcon, QAction, QGuiApplication
from PySide6.QtCore import Qt, QSize, QModelIndex, QThreadPool
from PySide6.QtWidgets import QFileSystemModel

from csvpath import CsvPaths
from csvpath.util.nos import Nos
from csvpath.util.path_util import PathUtility as pathu

from flightpath.dialogs.stage_data_dialog import StageDataDialog
from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.widgets.clickable_label import ClickableLabel
from flightpath.widgets.custom_tree_view import CustomTreeView
from flightpath.widgets.sidebars.sidebar_named_paths import SidebarNamedPaths
from flightpath.widgets.sidebars.sidebar_named_files import SidebarNamedFiles
from flightpath.widgets.file_tree_model.directory_filter_proxy_model import DirectoryFilterProxyModel
from flightpath.util.csvpath_loader import CsvpathLoader
from flightpath.util.help_finder import HelpFinder
from flightpath.util.os_utility import OsUtility as osut
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.message_utility import MessageUtility as meut

from flightpath.workers.precache_worker import PreCacheWorker

class Sidebar(QWidget):
    NEW_PROJECT = "Create new project"

    def __init__(self, main, role=0):
        super().__init__()
        self.main = main
        self.file_navigator = None
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
        #pixmap = QPixmap(fiut.make_app_path(f"assets{os.sep}logo.svg"))
        self.icon_label.setPixmap(pixmap)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.icon_label)
        self.icon_label.setStyleSheet("background-color: #ffffff;border:1px solid #c9c9c9;")
        #
        # cutted holds any cut-n-paste source path
        #
        self.cutted = None
        self.copied = None

        self.projects = QComboBox()
        size = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.projects.setSizePolicy(size)

        self._build_combo()
        self.projects.activated.connect(self.on_project_changed)
        self.projects.setStyleSheet("QComboBox { margin:1px; height:23px; padding-left:5px;}")
        #
        #
        #
        box = HelpIconPackager.add_help(
            main=self.main,
            widget=self.projects,
            on_help=self.on_click_cwd_help
        )
        layout.addWidget(box)
        #
        #
        #
        self._setup_tree()

        self.open_config_box = self._help_button(
            text="Open config",
            on_click=self.main.open_config,
            on_help=self.on_click_open_config_help
        )
        layout.addWidget(self.open_config_box)
        #
        # holds the last file right-clicked or None for the root whitespace or no previous rt-clicks
        #
        self._last_path = None
        self._last_file_index = None

        self.stage_dialog = None
        self.load_dialog = None

    def on_project_changed(self) -> None:
        proj = self.projects.currentText()
        if proj == self.main.state.current_project:
            #
            # no change
            #
            return
        if proj == self.NEW_PROJECT:
            proj, ok = meut.input(title="New Project", msg="Enter the new project's name")
            if ok and proj and proj.strip() != "":
                self.main.state.current_project = proj
                self._set_project_from_state()
            else:
                #
                # reset the combobox back to the current project
                #
                index = self.projects.findText(self.main.state.current_project)
                if index >= 0:
                    self.projects.setCurrentIndex(index)
            return
        self.main.state.current_project = proj
        self._set_project_from_state()

    def _set_project_from_state(self) -> None:
        self.main.load_state_and_cd()
        #
        # recreate all UI parts
        #
        self.main._csvpath_config = None
        self._setup_tree(replace=True)
        self._build_combo()
        #
        # reload everything on the right
        #
        self.main.renew_sidebar_archive()
        self.main.renew_sidebar_named_paths()
        self.main.renew_sidebar_named_files()
        #
        # sometimes it gets confused about the l&f
        #
        self.main.on_color_scheme_changed()


    def _build_combo(self) -> None:
        self.projects.clear()
        proj = self.main.state.current_project
        projs = os.path.join(self.main.state.home, self.main.state.projects_home)
        nos = Nos(projs)
        lst = nos.listdir(dirs_only=True)

        #
        # should not have to filter dirs because dirs_only=True, but stupidly the files
        # version of Nos only filters for files. to-be-fixed soon!
        #
        # csvpath has a clear test: /Users/davidkershaw/dev/csvpath/tests/dirs/test_dirs_local.py
        #
        #ps = [p for p in lst if not Nos(os.path.join(projs, p)).isfile()]
        #
        ps = lst
        ps.sort()
        for p in ps:
            self.projects.addItem(p)
            if p == proj:
                self.projects.setCurrentText(p)
        self.projects.insertSeparator(self.projects.count())
        self.projects.addItem("Create new project")


    @property
    def last_file_index(self) -> QModelIndex:
        return self._last_file_index

    @last_file_index.setter
    def last_file_index(self, i:QModelIndex) -> None:
        self._last_file_index = i

    def _help_button(self, *, text:str, on_click, on_help) -> QWidget:
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
        #
        # kickoff a precache worker to collect some info about files
        #
        worker = PreCacheWorker(self.main)
        self.threadpool = QThreadPool()
        self.threadpool.start(worker)

        old = self.file_navigator
        self.file_navigator = CustomTreeView()
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(self.main.state.cwd)

        exts = self.main.csvpath_config.csvpath_file_extensions + self.main.csvpath_config.csv_file_extensions
        exts = [f"*.{e}" for e in exts]
        #
        # we need json, of course. no reason to think it would be in csvpaths or csv extensions, but
        # checking just in case. there is a flattened json-ish format that could maybe come into play.
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
        #
        # TODO: find the current key dirs in config and filter out
        #
        self.file_model.setNameFilters(exts)
        self.file_model.setNameFilterDisables(False)
        #
        # exp. don't show the std background dirs
        #
        self.proxy_model = DirectoryFilterProxyModel(
            excluded_dirs=['config', 'logs', 'cache', 'archive', 'inputs', 'logs_bak'],
            sidebar=self
        )
        self.proxy_model.setSourceModel(self.file_model)
        self.proxy_model.sort(0, Qt.AscendingOrder)
        self.file_navigator.setModel(self.proxy_model)
        self.file_navigator.setRootIndex(self.proxy_model.mapFromSource(self.file_model.index(self.main.state.cwd)))
        #
        # end exp; orig 2 below
        #
        #self.file_navigator.setModel(self.file_model)
        #self.file_navigator.setRootIndex(self.file_model.setRootPath(self.main.state.cwd))
        #
        # this is alpha-sort descending. :/
        #
        self.file_navigator.setSortingEnabled(True)

        self._show_only_name_column_in_file_navigator(self.file_model, self.file_navigator)
        self.file_navigator.setHeaderHidden(True)
        self.file_navigator.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_navigator.customContextMenuRequested.connect(self._show_context_menu)
        self._setup_file_navigator_context_menu()
        if replace and old:
            self.layout().replaceWidget(old, self.file_navigator)
        else:
            self.layout().addWidget(self.file_navigator)

    def _setup_file_navigator_context_menu(self):
        """Create the context menu for the file navigator."""
        self.context_menu = QMenu(self)
        self.rename_action = QAction()
        self.open_location_action = QAction()
        self.open_project_dir_action = QAction()
        self.copy_path_action = QAction()
        self.copy_full_path_action = QAction()
        self.delete_action = QAction()
        self.new_file_action = QAction()
        self.save_file_action = QAction()
        self.new_folder_action = QAction()
        self.stage_data_action = QAction()
        self.load_paths_action = QAction()
        self.run_action = QAction()
        #
        #
        #
        self.line_number_action = QAction()
        #
        # cut and paste
        #
        self.cut_action = QAction()
        self.copy_action = QAction()
        self.paste_action = QAction()

        self.cut_action.setText("Cut")
        self.copy_action.setText("Copy")
        self.paste_action.setText("Paste")
        self.rename_action.setText("Rename")
        self.open_location_action.setText("Open directory")
        self.copy_path_action.setText("Copy relative path")
        self.copy_full_path_action.setText("Copy full path")
        self.open_project_dir_action.setText("Open project directory")
        self.delete_action.setText("Delete")
        self.new_file_action.setText("New file")
        self.save_file_action.setText("Save file")
        self.new_folder_action.setText("New folder")
        self.stage_data_action.setText("Stage data")
        self.load_paths_action.setText("Load csvpaths")
        #
        #
        #
        self.line_number_action.setText("line no")

        self.rename_action.triggered.connect(self._rename_file_navigator_item)
        self.open_location_action.triggered.connect(self._open_file_navigator_location)
        self.copy_path_action.triggered.connect(self._copy_path)
        self.copy_full_path_action.triggered.connect(self._copy_full_path)
        self.open_project_dir_action.triggered.connect(self._open_project_dir)
        self.delete_action.triggered.connect(self._delete_file_navigator_item)
        self.new_file_action.triggered.connect(self._new_file_navigator_item)
        self.save_file_action.triggered.connect(self._save_file_navigator_item)
        self.new_folder_action.triggered.connect(self._new_folder_navigator_item)
        self.stage_data_action.triggered.connect(self._stage_data)
        self.load_paths_action.triggered.connect(self._load_paths)
        self.cut_action.triggered.connect(self._cut)
        self.copy_action.triggered.connect(self._copy)
        self.paste_action.triggered.connect(self._paste)

        self.context_menu.addAction(self.save_file_action)
        self.context_menu.addAction(self.rename_action)
        self.context_menu.addAction(self.open_location_action)
        self.context_menu.addAction(self.copy_path_action)
        self.context_menu.addAction(self.copy_full_path_action)
        self.context_menu.addAction(self.open_project_dir_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.cut_action)
        self.context_menu.addAction(self.copy_action)
        self.context_menu.addAction(self.paste_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.delete_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.new_file_action)
        self.context_menu.addAction(self.new_folder_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.stage_data_action)
        self.context_menu.addAction(self.load_paths_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.line_number_action)

    def _show_context_menu(self, position):
        index = self.file_navigator.indexAt(position)
        global_pos = self.file_navigator.viewport().mapToGlobal(position)
        if index.isValid():
            self.rename_action.setVisible(True)
            self.open_location_action.setVisible(True)
            self.copy_path_action.setVisible(True)
            self.copy_full_path_action.setVisible(True)
            self.open_project_dir_action.setVisible(False)
            self.delete_action.setVisible(True)
            #
            # capture the location so we can create a new file or folder there
            #
            path = self.proxy_model.filePath(index)
            self._last_path = path
            nos = Nos(path)
            if nos.isfile():
                self.new_file_action.setVisible(False)
                self.new_folder_action.setVisible(False)
                ext = path[path.rfind(".")+1:]
                #
                # turn off load/stage/save operations. then (re)enable, if approprate.
                #
                self.save_file_action.setVisible(False)
                self.load_paths_action.setVisible(False)
                self.stage_data_action.setVisible(False)
                if ext in self.main.csvpath_config.csvpath_file_extensions or ext.lower() == "json":
                    self.load_paths_action.setVisible(True)
                elif ext in self.main.csvpath_config.csv_file_extensions:
                    self.stage_data_action.setVisible(True)
                if(
                   ext in self.main.csvpath_config.csvpath_file_extensions
                   or ext in self.main.csvpath_config.csv_file_extensions
                   or ext in ["md", "json", "txt"]
                ):
                    #
                    # always visible. shouldn't have to reset visible here, but for now it
                    # doesn't hurt to do it.
                    #
                    self.cut_action.setEnabled(True)
                    self.cut_action.setVisible(True)
                    self.copy_action.setEnabled(True)
                    self.copy_action.setVisible(True)
                    self.paste_action.setVisible(True)
                    if self.cutted is None and self.copied is None:
                        self.paste_action.setEnabled(False)
                    else:
                        #
                        # cannot paste onto a file. for now let's be explicit about that
                        #
                        self.paste_action.setEnabled(False)
                else:
                    self.cut_action.setEnabled(False)
                    self.copy_action.setEnabled(False)
                    self.paste_action.setEnabled(False)
                #
                #
                #
                if path.endswith(".csv"):
                    self.line_number_action.setVisible(True)
                    self.line_number_action.setEnabled(False)
                    csvpaths = CsvPaths()
                    #
                    # we aren't necessarily using cache -- tho in local projects, why not? so we
                    # only set a path and use_cache temp. this whole operation is not super
                    # efficient but it won't be noticable to the user and this settings shell game
                    # doesn't add much. longer term a file info panel in rt-col or a floating label?
                    #
                    cdir = csvpaths.config.get(section="cache", name="path")
                    cuse = csvpaths.config.get(section="cache", name="use_cache")
                    csvpaths.config.set(section="cache", name="path", value=f"{self.main.state.cwd}{os.sep}cache")
                    csvpaths.config.set(section="cache", name="use_cache", value=f"yes")
                    c = csvpaths.file_manager.lines_and_headers_cacher.get_new_line_monitor(path).physical_end_line_count
                    self.line_number_action.setText(f"{c} lines")
                else:
                    self.line_number_action.setVisible(False)

            else:
                self.line_number_action.setVisible(False)
                #
                # paste only if dir and cutted. cut only if file.
                #
                if self.cutted is not None or self.copied is not None:
                    self.paste_action.setEnabled(True)
                else:
                    self.paste_action.setEnabled(False)
                self.cut_action.setEnabled(False)
                self.copy_action.setEnabled(False)
                #
                self.new_file_action.setVisible(True)
                self.new_folder_action.setVisible(True)
                self.load_paths_action.setVisible(True)
                self.stage_data_action.setVisible(True)
        else:
            #
            # was in the tree view, but not over an item. this is where the new option
            # needs to happen.
            #
            self.rename_action.setVisible(False)

            self.paste_action.setVisible(True)
            if self.cutted or self.copied:
                self.paste_action.setEnabled(True)
            else:
                self.paste_action.setEnabled(False)

            self.open_location_action.setVisible(False)
            self.copy_path_action.setVisible(False)
            self.copy_full_path_action.setVisible(False)
            self.copy_full_path_action.setVisible(False)
            self.open_project_dir_action.setVisible(True)

            self.delete_action.setVisible(False)
            self.new_file_action.setVisible(True)
            self.new_folder_action.setVisible(True)
            self.load_paths_action.setVisible(False)
            self.stage_data_action.setVisible(False)
            #
            #
            #
            self.line_number_action.setVisible(False)

            #
            # clear so we know to create new files or folders at the root
            #
            self._last_path = None
        self.context_menu.exec(global_pos)

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

    def _stage_data(self) -> None:
        index = self.file_navigator.currentIndex()
        if index.isValid():
            path = self.proxy_model.filePath(index)
            self.stage_dialog = StageDataDialog(path=path, parent=self)
            self.stage_dialog.show_dialog()
        else:
            ... # should never happen, but what if it did?

    def _cut(self) -> None:
        index = self.file_navigator.currentIndex()
        if index.isValid():
            path = self.proxy_model.filePath(index)
            self.cutted = path

    def _copy(self) -> None:
        index = self.file_navigator.currentIndex()
        if index.isValid():
            path = self.proxy_model.filePath(index)
            self.copied = path

    def _paste(self) -> None:
        if self.cutted is None and self.copied is None:
            #
            # can't happen
            #
            return
        index = self.file_navigator.selectionModel().selectedIndexes()
        index = index[0] if len(index) > 0 else None
        path = None
        if index and index.isValid():
            path = self.proxy_model.filePath(index)
        else:
            path = self.main.state.cwd
        if self.cutted:
            name = os.path.basename(self.cutted)
            path = os.path.join(path, name)
            nos = Nos(self.cutted)
            nos.rename(path)
        elif self.copied:
            name = os.path.basename(self.copied)
            path = fiut.deconflicted_path(path, name)
            nos = Nos(self.copied)
            # disambiguate here
            nos.copy(path)
        self.cutted = None
        self.copied = None

    def _load_paths(self) -> None:
        index = self.file_navigator.currentIndex()
        if index.isValid():
            path = self.proxy_model.filePath(index)
            loader = CsvpathLoader(main=self.main)
            loader.load_paths(path)

    def _run_paths(self) -> None:
        ...

    def _renew_sidebars(self) -> None:
        #
        # TODO: we recreate all the trees. very bad idea due to slow refresh from remote.
        # but for now it should work. refreshing named_files is probably fair, but that's
        # also tricky because we'd want to recreate the opened/closed state of the folders
        # and if we did that the refresh might slow down potentially a lot. so long-term,
        # seems like we should capture what is registered and manually add it. no fun. :/
        #
        # we're only actually doing named_paths here. what's up with that?
        #
        self.main.sidebar_rt_mid = SidebarNamedPaths(main=self.main, config=self.main.csvpath_config, role=2)
        self.main.rt_col.replaceWidget(1, self.main.sidebar_rt_mid)
        #self.main.sidebar_rt_mid.view.clicked.connect(self.main.on_named_paths_tree_click)


    def do_stage(self) -> None:
        template = self.stage_dialog.template_ctl.text()
        template = template.strip()
        if template == "":
            template = None
        if template and not template.endswith(":filename"):
            meut.message(msg="The :filename token must be the last component of the template", title="Incomplete")
            return
            #
            # there's a fair chance this will be the desired template, but could
            # easily not be. regardless, we need a :filename and we can delete and
            # redo more simply than we can error and recover.
            #
            template = f"{template}/:filename"
        named_file_name = self.stage_dialog.named_file_name_ctl.text()
        recurse = self.stage_dialog.recurse_ctl.isChecked()
        name = self.stage_dialog.path
        nos = Nos(name)
        paths = CsvPaths()
        #
        # have to override the filesystem prohibit because it doesn't make sense
        # here. we are all local file-based atm and also control config.
        #
        local = paths.config.set(section="inputs", name="allow_local_files", value=True)
        try:
            if nos.isfile():
                paths.file_manager.add_named_file(name=named_file_name, path=name, template=template)
            else:
                if self.stage_dialog.separate_ctl.isChecked():
                    paths.file_manager.add_named_files_from_dir(name=None, dirname=name, template=template, recurse=recurse)
                else:
                    if not named_file_name or named_file_name.strip() == "":
                        meut.message(title="No name given", msg="You must provide a named-file name")
                        return
                    paths.file_manager.add_named_files_from_dir(name=named_file_name, dirname=name, template=template, recurse=recurse)
        except Exception as e:
            meut.message(title="Stage error", msg=f"{e}")
            return
        #
        # TODO: we recreate all the trees. very bad idea due to slow refresh from remote.
        # but for now it should work. refreshing named_files is probably fair, but that's
        # also tricky because we'd want to recreate the opened/closed state of the folders
        # and if we did that the refresh might slow down potentially a lot. so long-term,
        # seems like we should capture what is registered and manually add it. no fun. :/
        #
        self.main.sidebar_rt_top = SidebarNamedFiles(main=self.main, config=self.main.csvpath_config, role=1)
        self.main.rt_col.replaceWidget(0, self.main.sidebar_rt_top)
        #self.main.sidebar_rt_top.view.clicked.connect(self.main.on_named_file_tree_click)
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

    def _rename_file_navigator_item(self):
        index = self.file_navigator.currentIndex()
        if index.isValid():
            path = self.proxy_model.filePath(index)
            dir_name = os.path.dirname(path)
            name = os.path.basename(path)
            dialog = QInputDialog()
            dialog.setFixedSize(QSize(420, 125))
            dialog.setLabelText("Enter new name:")
            dialog.setTextValue(name)
            ok = dialog.exec()
            new_name = dialog.textValue()

            if ok and new_name and new_name.strip() != "" and new_name != name:
                if new_name.find(os.sep) > -1:
                    new_dir = os.path.dirname(new_name)
                    np = os.path.join(dir_name, new_dir)
                    np = os.path.normpath(np)
                    if np.startswith( self.main.state.cwd ):
                        try:
                            nos = Nos( np )
                            if not nos.exists():
                                nos.makedirs()
                        except Exception as e:
                            msg_box = QMessageBox()
                            msg_box.setIcon(QMessageBox.Critical)
                            msg_box.setWindowTitle("Path error")
                            msg_box.setText(f"Error: invalid path: {np}")
                            msg_box.setStandardButtons(QMessageBox.Ok)
                            msg_box.exec()
                            return
                    else:
                        msg_box = QMessageBox()
                        msg_box.setIcon(QMessageBox.Critical)
                        msg_box.setWindowTitle("Path error")
                        msg_box.setText(f"Error: invalid path: {np}")
                        msg_box.setStandardButtons(QMessageBox.Ok)
                        msg_box.exec()
                        return
                nos = Nos(path).rename(os.path.join( dir_name, new_name) )

    def _new_folder_navigator_item(self):
        dialog = QInputDialog()
        dialog.setFixedSize(QSize(420, 125))
        dialog.setLabelText("Enter the new folder name: ")
        ok = dialog.exec()
        new_name = dialog.textValue()

        if ok and new_name:
            b, msg = self._valid_new_folder(new_name)
            if b is True:
                try:
                    if not new_name.startswith(self.main.state.cwd):
                        if self._last_path is None:
                            new_name = os.path.join(self.main.state.cwd, new_name)
                        else:
                            n = os.path.join(self.main.state.cwd, self._last_path)
                            new_name = os.path.join(n, new_name)
                    #
                    # would templates add any value? e.g. a blank file with ---- CSVPATH ----
                    #
                    # TODO: use Nos
                    #
                    os.mkdir(new_name)
                except PermissionError:
                    QMessageBox.warning(self, self.tr("Error"), self.tr("Operation not permitted."))
                except OSError:
                    QMessageBox.warning(self, self.tr("Error"), self.tr("File with this name already exists."))
            else:
                #
                # show a simple error msg dialog. may look significantly different from the modal, but
                # that is fine for now.
                #
                self.window().statusBar().showMessage(self.tr("Bad folder name"))
                button = QMessageBox.critical(
                    self,
                    "Cannot create folder",
                    msg,
                    buttons=QMessageBox.Cancel | QMessageBox.Retry,
                    defaultButton=QMessageBox.Cancel
                )
                if button == QMessageBox.Retry:
                    self._new_folder_navigator_item()
                return

    def _valid_new_folder(self, name:str) -> tuple[bool,str]:
        b = name.find(".") == -1
        if b:
            return b, "Ok"
        return b, "Failed"

    def _save_file_navigator_item(self):
        self.main.content.csvpath_source_view.text_edit.on_save()

    def _new_file_navigator_item(self):
        dialog = QInputDialog()
        dialog.setFixedSize(QSize(420, 125))
        dialog.setLabelText("Enter the new file's name:")
        ok = dialog.exec()
        new_name = dialog.textValue()
        if ok and new_name:
            b, msg = self._valid_new_file(new_name)
            if b is True:
                ns = fiut.split_filename(new_name)
                #
                # if we're creating a JSON file we need to populate with a {} or []
                #
                content = ""
                if new_name.endswith(".json"):
                    items = ["{}", "[]"]
                    item, ok = QInputDialog.getItem(self, "Data structure", "Start with", items, 0, False)
                    if ok and item:
                        content = item
                elif new_name.endswith(".md"):
                    content = """# Title
*(hit control-t to toggle to raw markdown editing)*
                    """
                elif ns[1] in self.main.csvpath_config.csvpath_file_extensions:
                    testdata = ""
                    _ = os.path.join(self.main.state.cwd, "examples/test.csv")
                    if Nos(_).exists():
                        testdata = "examples/test.csv"

                    content = f"""~
   id: hello world
   test-data: {testdata}
~

$[*][ print("hello world") ]"""

                try:
                    if not new_name.startswith(self.main.state.cwd):
                        if self._last_path is None:
                            new_name = os.path.join(self.main.state.cwd, new_name)
                        else:
                            n = os.path.join(self.main.state.cwd, self._last_path)
                            new_name = os.path.join(n, new_name)
                    with open(new_name, "w", encoding="utf-8") as file:
                        file.write(content)
                #
                # create file
                #
                except PermissionError:
                    QMessageBox.warning(self, "Error", "Operation not permitted.")
                except OSError:
                    QMessageBox.warning(self, "Error", "File with this name already exists.")
            else:
                #
                # show a simple error msg dialog. may look significantly different from the modal, but
                # that is fine for now.
                #
                self.window().statusBar().showMessage(self.tr("Bad file name"))
                button = QMessageBox.critical(
                    self,
                    "Cannot create file",
                    msg,
                    buttons=QMessageBox.Cancel | QMessageBox.Retry,
                    defaultButton=QMessageBox.Cancel
                )
                if button == QMessageBox.Retry:
                    self._new_file_navigator_item()
                return

    def _valid_new_file(self, name:str) -> tuple[bool,str]:
        if name is None or name.strip() == "":
            return False, "Name cannot be empty"
        if (
            (name.find("/") > -1 or name.find("\\") > -1)
            and not ( name.startswith(self.main.state.cwd) or name.startswith(f".{os.sep}") )
        ):
            return False, "File must be in or below the working directory"
        if name.find(".", 1) == -1:
            return False, "File name must have an extension recognized by CsvPath"
        ext = name[name.rfind(".")+1:]
        if ext == "json":
            return True, "Ok"
        #
        # do we want to allow creating html files?  that's a whole can of worms.
        # maybe just display them. perhaps also editing, to a degree?
        #
        if ext in ["md", "txt"]:
            return True, "Ok"
        if ( ext not in self.main.csvpath_config.csvpath_file_extensions
             and ext not in self.main.csvpath_config.csv_file_extensions
        ):
            return False, "File name must have an extension configured for csvpaths or data files"

        if ext in self.main.csvpath_config.csv_file_extensions:
            meut.message( title="Data file", msg="You are creating an empty data file that must be edited outside of FlightPath" )

        return True, "Ok"

    def _open_file_navigator_location(self):
        index = self.file_navigator.currentIndex()
        #
        # if not valid we clicked on below-tree whitespace and get the
        # current working directory. however, this doesn't seem to happen at least on windows.
        # today we're getting the current selection which is always something, so no longer
        # the expected behavior.
        #
        if index.isValid():
            path = self.proxy_model.filePath(index)
        else:
            path = self.main.state.cwd
        path = pathu.resep(path)
        nos = Nos(path)
        if nos.isfile():
            path = os.path.dirname(path)
        o = osut.file_system_open_cmd()
        o = f'{o} "{path}"'
        os.system(o)

    def _copy_path(self):
        index = self.file_navigator.currentIndex()
        if index.isValid():
            path = self.proxy_model.filePath(index)
        else:
            raise RuntimeError("An item must be clicked to copy a relative path")
        path = pathu.resep(path)
        if path.startswith( self.main.state.cwd ):
            path = path[len(self.main.state.cwd)+1:]
        else:
            raise ValueError(f"Path must start with {self.main.state.cwd}. {path} does not.")
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(path)

    def _copy_full_path(self):
        index = self.file_navigator.currentIndex()
        if index.isValid():
            path = self.proxy_model.filePath(index)
        else:
            path = self.main.state.cwd
        path = pathu.resep(path)
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(path)

    def _open_project_dir(self):
        path = self.main.state.cwd
        path = pathu.resep(path)
        o = osut.file_system_open_cmd()
        o = f'{o} "{path}"'
        print(f"_open_project_dir: o: {o}")
        os.system(o)

    def _delete_file_navigator_item(self):
        index = self.file_navigator.currentIndex()
        if index.isValid():
            path = self.proxy_model.filePath(index)
            path = str(path)
            is_selected = self.window().selected_file_path == path
            confirm = QMessageBox.question(
                self,
                self.tr("Delete"),
                self.tr(f"Are you sure you want to delete {path}?"),
                QMessageBox.Yes | QMessageBox.No,
            )
            if confirm == QMessageBox.Yes:
                try:
                    Nos(path).remove()
                except OSError as e:
                    QMessageBox.warning(self, self.tr("Error"), str(e))
                else:
                    if is_selected:
                        self.window().show_welcome_screen()
                    self.window().statusBar().showMessage(f"{path} deleted successfuly.")

    def _show_only_name_column_in_file_navigator(self, file_model, file_navigator):
        for column in range(file_model.columnCount()):
            if column != 0:  # 0 is the name column
                file_navigator.setColumnHidden(column, True)


