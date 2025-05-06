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

from PySide6.QtGui import QPixmap, QIcon, QAction
from PySide6.QtCore import Qt, QSize, QSortFilterProxyModel, QModelIndex
from PySide6.QtWidgets import QFileSystemModel

from csvpath import CsvPaths
from csvpath.util.nos import Nos

from flightpath.widgets.clickable_label import ClickableLabel
from flightpath.widgets.custom_tree_view import CustomTreeView
from flightpath.dialogs.stage_data_dialog import StageDataDialog
from flightpath.dialogs.load_paths_dialog import LoadPathsDialog
from flightpath.util.os_utility import OsUtility as osut
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.widgets.plus_help import HelpIconPackager
from flightpath.util.help_finder import HelpFinder

from flightpath.widgets.sidebars.sidebar_named_paths import SidebarNamedPaths
from flightpath.widgets.sidebars.sidebar_named_files import SidebarNamedFiles
from flightpath.widgets.file_tree_model.directory_filter_proxy_model import DirectoryFilterProxyModel

class Sidebar(QWidget):

    def __init__(self, main, role=0):
        super().__init__()
        self.main = main
        self.file_navigator = None
        self.setMinimumWidth(300)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setSpacing(0)
        layout.setContentsMargins(4, 3, 1, 3)
        self.icon_label = ClickableLabel()
        pixmap = QPixmap(fiut.make_app_path(f"assets{os.sep}logo.svg"))
        self.icon_label.setPixmap(pixmap)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.icon_label)
        self.icon_label.setStyleSheet("background-color: #ffffff;border:1px solid #c9c9c9;")
        #
        # cutted holds any cut-n-paste source path
        #
        self.cutted = None
        self.copied = None

        self.cwd_box = self._help_button(
            text="Set working directory",
            on_click=self.main.on_set_cwd_click,
            on_help=self.on_click_cwd_help
        )
        layout.addWidget(self.cwd_box)

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

    @property
    def last_file_index(self) -> QModelIndex:
        return self._last_file_index

    @last_file_index.setter
    def last_file_index(self, i:QModelIndex) -> None:
        self._last_file_index = i

    def _help_button(self, *, text:str, on_click, on_help) -> QWidget:
        self.button_copy_in = QPushButton()
        self.button_copy_in.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        box = HelpIconPackager.add_help(main=self.main, widget=self.button_copy_in, on_help=on_help)
        self.button_copy_in.setText(text)
        self.button_copy_in.clicked.connect(on_click)
        return box

    def on_click_cwd_help(self) -> None:
        md = HelpFinder(main=self.main).help("sidebar/cwd.md")
        self.main.get_help_tab().setMarkdown(md)
        if not self.main.is_showing_help():
            self.main.on_click_help()

    def on_click_open_config_help(self) -> None:
        md = HelpFinder(main=self.main).help("sidebar/open_config.md")
        self.main.get_help_tab().setMarkdown(md)
        if not self.main.is_showing_help():
            self.main.on_click_help()

    def _setup_tree(self) -> None:
        self.file_navigator = CustomTreeView()
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(self.main.state.cwd)

        exts = self.main.csvpath_config.csvpath_file_extensions + self.main.csvpath_config.csv_file_extensions
        exts = [f"*.{e}" for e in exts]
        if "*.json" not in exts:
            exts.append("*.json")
        #
        # TODO: find the current key dirs in config and filter out
        #
        self.file_model.setNameFilters(exts)
        self.file_model.setNameFilterDisables(False)

        #
        # this works as far as the ascending alpha sort, but it does a segmention fault 11 when
        # you click on a file. could be similar to the way we needed the trap dict in an
        # early version of the tree model?
        #
        """
        #
        # exp
        #
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.file_model)

        self.proxy_model.sort(0, Qt.AscendingOrder)

        self.file_navigator.setModel(self.proxy_model)
        self.file_navigator.setRootIndex(self.proxy_model.mapFromSource(self.file_model.index(self.main.state.cwd)))
        print(f"setupdtr: {self.main.state.cwd}")
        #
        # end exp
        #
        """

        #
        # exp
        #
        self.proxy_model = DirectoryFilterProxyModel(excluded_dirs=['config', 'logs', 'cache', 'archive', 'inputs'], sidebar=self)
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
        self.layout().addWidget(self.file_navigator)


    def _setup_file_navigator_context_menu(self):
        """Create the context menu for the file navigator."""
        self.context_menu = QMenu(self)

        self.rename_action = QAction()
        self.open_location_action = QAction()
        self.delete_action = QAction()
        self.new_file_action = QAction()
        self.save_file_action = QAction()
        self.new_folder_action = QAction()
        self.stage_data_action = QAction()
        self.load_paths_action = QAction()

        self.run_action = QAction()
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
        self.delete_action.setText("Delete")
        self.new_file_action.setText("New file")
        self.save_file_action.setText("Save file")
        self.new_folder_action.setText("New folder")
        self.stage_data_action.setText("Stage data")
        self.load_paths_action.setText("Load csvpaths")

        self.rename_action.triggered.connect(self._rename_file_navigator_item)
        self.open_location_action.triggered.connect(self._open_file_navigator_location)
        self.delete_action.triggered.connect(self._delete_file_navitagor_item)
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

    def _show_context_menu(self, position):
        index = self.file_navigator.indexAt(position)
        global_pos = self.file_navigator.viewport().mapToGlobal(position)
        if index.isValid():
            self.rename_action.setVisible(True)
            self.open_location_action.setVisible(True)
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
                # if a csvpath file is open and changed we need to offer to save it
                #
                if ext in self.main.csvpath_config.csvpath_file_extensions:
                    i = self.main.content.tab_widget.currentIndex()
                    if i == 2 and not self.main.content.csvpath_source_view.saved:
                        self.save_file_action.setVisible(True)

            else:
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

            self.open_location_action.setVisible(True)
            self.delete_action.setVisible(False)
            self.new_file_action.setVisible(True)
            self.new_folder_action.setVisible(True)
            self.load_paths_action.setVisible(False)
            self.stage_data_action.setVisible(False)
            #
            # clear so we know to create new files or folders at the root
            #
            self._last_path = None
        self.context_menu.exec(global_pos)

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
            #path = os.path.join(path, name)
            nos = Nos(self.copied)
            # disambiguate here
            nos.copy(path)
        self.cutted = None
        self.copied = None

    def _load_paths(self) -> None:
        index = self.file_navigator.currentIndex()
        if index.isValid():
            path = self.proxy_model.filePath(index)
            self.load_dialog = LoadPathsDialog(path=path, parent=self)
            self.load_dialog.show_dialog()
        else:
            ... # should never happen, but what if it did?

    def _run_paths(self) -> None:
        ...

    def do_load(self) -> None:
        template = self.load_dialog.template_ctl.text()
        if template and template.strip() == "":
            template = None
        named_paths_name = self.load_dialog.named_paths_name_ctl.text()
        name = self.load_dialog.path
        nos = Nos(name)
        paths = CsvPaths()
        #
        # if the named-paths name exists, warn the user that they are adding a named-path to the group
        #
        if paths.paths_manager.has_named_paths(named_paths_name):
            confirm = QMessageBox.question(
                self,
                self.tr("Add Paths"),
                self.tr("Are you sure you want to add these csvpaths to an existing named-paths group?"),
                QMessageBox.Yes | QMessageBox.No,
            )
            if confirm == QMessageBox.No:
                return
        if nos.isfile():
            ext = name[name.rfind(".")+1:]
            if ext in self.main.csvpath_config.csvpath_file_extensions:
                paths.paths_manager.add_named_paths_from_file(name=named_paths_name, file_path=name, template=template)
            elif name.endswith(".json"):
                paths.paths_manager.add_named_paths_from_json(file_path=name)
            else:
                raise ValueError(f"Unknown file type: {name}")
        else:
            paths.paths_manager.add_named_paths_from_dir(name=named_paths_name, directory=name, template=template)
        #
        # TODO: we recreate all the trees. very bad idea due to slow refresh from remote.
        # but for now it should work. refreshing named_files is probably fair, but that's
        # also tricky because we'd want to recreate the opened/closed state of the folders
        # and if we did that the refresh might slow down potentially a lot. so long-term,
        # seems like we should capture what is registered and manually add it. no fun. :/
        #
        self.main.sidebar_rt_mid = SidebarNamedPaths(main=self.main, config=self.main.csvpath_config, role=2)
        self.main.rt_col.replaceWidget(1, self.main.sidebar_rt_mid)
        self.main.sidebar_rt_mid.view.clicked.connect(self.main.on_named_paths_tree_click)
        #
        # TODO: add delete later?
        #
        self.load_dialog.close()
        self.load_dialog.deleteLater()
        self.load_dialog = None

    def do_stage(self) -> None:
        template = self.stage_dialog.template_ctl.text()
        if template and template.strip() == "":
            template = None
        if template and template.find(":filename") == -1:
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
        if nos.isfile():
            paths.file_manager.add_named_file(name=named_file_name, path=name, template=template)
        else:
            paths.file_manager.add_named_files_from_dir(name=named_file_name, dirname=name, template=template, recurse=recurse)
        #
        # TODO: we recreate all the trees. very bad idea due to slow refresh from remote.
        # but for now it should work. refreshing named_files is probably fair, but that's
        # also tricky because we'd want to recreate the opened/closed state of the folders
        # and if we did that the refresh might slow down potentially a lot. so long-term,
        # seems like we should capture what is registered and manually add it. no fun. :/
        #
        self.main.sidebar_rt_top = SidebarNamedFiles(main=self.main, config=self.main.csvpath_config, role=1)
        self.main.rt_col.replaceWidget(0, self.main.sidebar_rt_top)
        self.main.sidebar_rt_top.view.clicked.connect(self.main.on_named_file_tree_click)
        #
        #
        #
        self.stage_dialog.close()
        #
        # TODO: add delete later?
        #
        self.stage_dialog.deleteLater()
        self.stage_dialog = None

    def _rename_file_navigator_item(self):
        index = self.file_navigator.currentIndex()
        if index.isValid():
            path = self.proxy_model.filePath(index)
            name = os.path.dirname(path)
            new_name, ok = QInputDialog.getText(self, self.tr("Rename"), self.tr("Enter new name:"), text=name)
            if ok and new_name:
                nos = Nos(path).rename(os.path.join( os.path.dirname(path), new_name))

    def _new_folder_navigator_item(self):
        new_name, ok = QInputDialog.getText(self, self.tr("New folder"), self.tr("Enter the new folder name: "), text="")
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
        new_name, ok = QInputDialog.getText(self, self.tr("New file"), self.tr("Enter the new file name: "), text="")
        if ok and new_name:
            b, msg = self._valid_new_file(new_name)
            if b is True:
                try:
                    if not new_name.startswith(self.main.state.cwd):
                        if self._last_path is None:
                            new_name = os.path.join(self.main.state.cwd, new_name)
                        else:
                            n = os.path.join(self.main.state.cwd, self._last_path)
                            new_name = os.path.join(n, new_name)
                    with open(new_name, "w", encoding="utf-8") as file:
                        file.write("")
                #
                # create file
                #
                except PermissionError:
                    QMessageBox.warning(self, self.tr("Error"), self.tr("Operation not permitted."))
                except OSError:
                    QMessageBox.warning(self, self.tr("Error"), self.tr("File with this name already exists."))
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
        if ext not in self.main.csvpath_config.csvpath_file_extensions and ext not in self.main.csvpath_config.csv_file_extensions:
            return False, "File name must have an extension configured for csvpaths or data files"
        return True, "Ok"

    def _open_file_navigator_location(self):
        index = self.file_navigator.currentIndex()
        #
        # if not valid we clicked on below-tree whitespace and get the
        # current working directory
        #
        if index.isValid():
            path = self.proxy_model.filePath(index)
        else:
            path = self.main.state.cwd
        folder = os.path.dirname(path)
        o = osut.file_system_open_cmd()
        os.system(f'{o} "{folder}"')

    def _delete_file_navitagor_item(self):
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


