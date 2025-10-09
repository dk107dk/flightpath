import sys
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QPushButton,
    QWidget,
    QComboBox,
    QMenu,
    QMessageBox,
    QVBoxLayout
)

from PySide6.QtGui import QPixmap, QIcon, QAction
from PySide6.QtCore import Qt, QSize, QModelIndex
from PySide6.QtWidgets import QFileSystemModel, QTreeView, QAbstractItemView, QSizePolicy, QHeaderView

from csvpath import CsvPaths
from csvpath.util.nos import Nos
from csvpath.util.config import Config
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter

from flightpath.widgets.clickable_label import ClickableLabel

from flightpath.widgets.file_tree_model.treemodel import TreeModel
from flightpath.dialogs.new_run_dialog import NewRunDialog

from flightpath.widgets.help.plus_help import HelpHeaderView
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.message_utility import MessageUtility as meut
from flightpath.editable import EditStates

class SidebarNamedPaths(QWidget):

    def __init__(self, *, main, role=1, config:Config):
        super().__init__()
        self.main = main
        self.config = config
        self.setMinimumWidth(300)
        self.new_run_action = None
        self.copy_action = None
        self.delete_action = None
        self.view = None
        self.setup()

    def setup(self) -> None:
        try:
            named_paths_path = self.config.get(section="inputs", name="csvpaths")
            nos = Nos(named_paths_path)
            layout = self.layout()
            if layout is None:
                layout = QVBoxLayout()
            layout.setSpacing(0)
            layout.setContentsMargins(1, 1, 1, 1)
            if nos.dir_exists():
                #
                #
                #
                nos.makedir()
            self.view = QTreeView()
            self.view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
            self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.view.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            self.view.setWordWrap(False)
            self.view.setAnimated(False)
            self.view.setAllColumnsShowFocus(True)
            self.view.setAutoScroll(True)
            self.view.setIndentation(20)
            self.view.setColumnWidth(0, 250)
            header = self.view.header()
            header.setStretchLastSection(True)
            header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            self.model = TreeModel(["Csvpath groups"], nos, self, title="Loaded named-paths groups", sidebar=self)
            self.model.set_style(self.view.style())
            self.view.setModel(self.model)
            self.view.updateGeometries()
            layout.addWidget(self.view)
            #
            #
            #
            self.view.setHeader(HelpHeaderView(self.view, on_help=self.main.helper.on_click_named_paths_help))
            self.view.header().setSectionResizeMode(0, QHeaderView.Stretch)
            self.view.header().setFixedHeight(24)
            self.view.header().setStyleSheet("QHeaderView {font-size:13px}")
            #
            #
            #
            self.view.setContextMenuPolicy(Qt.CustomContextMenu)
            self.view.customContextMenuRequested.connect(self._show_context_menu)
            self._setup_view_context_menu()
            #
            # moved from main
            #
            self.view.clicked.connect(self.on_named_paths_tree_click)
            self.setLayout(layout)
        except Exception as e:
            meut.message(title=f"{type(e)} error loading named-paths", msg=f"Named-paths error: {e}")


    #
    # moved from main
    #
    def on_named_paths_tree_click(self, index):
        self.main.selected_file_path = self.model.filePath(index)
        nos = Nos(self.main.selected_file_path)
        if not nos.isfile():
            ...
            #self._show_welcome_but_do_not_deselect()
        else:
            self.main.read_validate_and_display_file(editable=EditStates.UNEDITABLE)
            self.main.statusBar().showMessage(f"  {self.main.selected_file_path}")


    def update_style(self) -> None:
        try:
            self.model.set_style(self.view.style())
        except Exception as e:
            print(f"error in named-paths: {type(e)}: {e}")

    def refresh(self) -> None:
        if self.view:
            layout = self.layout()  # Get the existing layout
            if layout:
                layout.removeWidget(self.view)
            self.view.deleteLater()  # Delete the old widget
            self.setup()

    def _setup_view_context_menu(self):
        self.context_menu = QMenu(self)

        self.new_run_action = QAction()
        self.new_run_action.setText(self.tr("New run"))
        self.copy_action = QAction()
        self.copy_action.setText(self.tr("Copy to working dir"))
        self.delete_action = QAction()
        self.delete_action.setText(self.tr("Permanent delete"))

        self.new_run_action.triggered.connect(self._new_run)
        self.copy_action.triggered.connect(self._copy_paths_back_to_cwd)
        self.delete_action.triggered.connect(self._delete_file_navigator_item)

        self.context_menu.addAction(self.new_run_action)
        self.context_menu.addAction(self.copy_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.delete_action)


    def _copy_paths_back_to_cwd(self) -> None:
        from_index = self.view.currentIndex()
        if from_index.isValid():
            from_path = self.model.filePath(from_index)
            #from_nos = Nos(from_path)
            to_index = self.main.sidebar.file_navigator.currentIndex()

            to_path = None
            if to_index.isValid():
                to_path = self.main.sidebar.proxy_model.filePath(to_index)
            else:
                to_path = self.main.state.cwd

            to_nos = Nos(to_path)
            if to_nos.isfile():
                QMessageBox.warning(self, "Error", f"Cannot copy file to {to_nos.path}")
                return
            to_path = fiut.deconflicted_path(to_path, f"{os.path.basename(from_path)}")
            to_nos.path = to_path
            if to_nos.exists():
                #
                # this won't realistically happen
                #
                QMessageBox.warning(self, "Error", f"Cannot copy file to {to_nos.path}")
            #
            #from_nos.copy(to_nos.path)
            #
            # nos copy only works if we're copying to the same backend, which we won't always be.
            # so we use reader/writers. leaving as a reminder.
            #
            with DataFileReader(from_path) as ffrom:
                with DataFileWriter(path=to_path) as tto:
                    tto.write(ffrom.read())
        else:
            QMessageBox.warning(self, "Error", "Cannot copy item")

    @property
    def _paths_root(self) -> str:
        return self.main.csvpath_config.get(section="inputs", name="csvpaths")

    def _new_run(self) -> None:
        index = self.view.currentIndex()
        path = self.model.filePath(index)
        named_paths = None
        if path.startswith(self._paths_root):
            named_paths = path[len(self._paths_root) + 1:]
        else:
            # shouldn't happen but what if it did?
            ...
        self.new_run_dialog = NewRunDialog(parent=self, named_paths=named_paths)
        #
        # check if there is a description.json. if there is, check if
        # there is a template for the group. if so, add to dialog.
        #
        t = CsvPaths().paths_manager.get_template_for_paths(named_paths)
        if t:
            self.new_run_dialog.template = t
            self.new_run_dialog.template_ctl.setText(t)
        self.main.show_now_or_later(self.new_run_dialog)
        #self.new_run_dialog.show()


    def _show_context_menu(self, position) -> None:
        index = self.view.indexAt(position)
        path = None
        if index.isValid():
            global_pos = self.view.viewport().mapToGlobal(position)
            path = self.model.filePath(index)
            self._last_path = path
            nos = Nos(path)
            #
            # individual files may not be deleted, but we can allow dir deletes for cleanup
            #
            if nos.isfile():
                self.delete_action.setVisible(False)
                self.new_run_action.setVisible(False)
                self.copy_action.setVisible(True)
            else:
                self.delete_action.setVisible(True)
                self.new_run_action.setVisible(True)
                self.copy_action.setVisible(False)
            if path and ( path.endswith("manifest.json") or path.endswith(".db") ):
                self.delete_action.setVisible(False)
                self.new_run_action.setVisible(False)
                self.copy_action.setVisible(True)
            if global_pos:
                self.context_menu.exec(global_pos)

    def _delete_file_navigator_item(self):
        index = self.view.currentIndex()
        if index.isValid():
            path = self.model.filePath(index)
            nos = Nos(path)
            confirm = QMessageBox.question(
                self,
                self.tr("Delete"),
                self.tr(f"Permanently delete {path}?"),
                QMessageBox.Yes | QMessageBox.No,
            )
            if confirm == QMessageBox.Yes:
                try:
                    nos.remove()
                except OSError as e:
                    QMessageBox.warning(self, self.tr("Error"), str(e))
                else:
                    #
                    # TODO: this will have to change because we don't want to dismiss
                    # content that is being worked on from the working dir side
                    #
                    #if is_selected:
                    #    self.window().show_welcome_screen()
                    self.window().statusBar().showMessage(f"{path} deleted")
                    #
                    # TODO: we recreate all the trees. very bad idea due to slow refresh from remote.
                    # but for now it should work. refreshing named_files is probably fair, but that's
                    # also tricky because we'd want to recreate the opened/closed state of the folders
                    # and if we did that the refresh might slow down potentially a lot. so long-term,
                    # seems like we should capture what is registered and manually add it. no fun. :/
                    #
                    #self.main._setup_central_widget()
                    self.main.renew_sidebar_named_paths()




