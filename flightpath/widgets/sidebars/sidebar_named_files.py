import sys
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QPushButton,
    QWidget,
    QMenu,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QApplication
)

from PySide6.QtGui import QPixmap, QIcon, QAction
from PySide6.QtCore import Qt, QSize, QModelIndex
from PySide6.QtWidgets import QFileSystemModel, QTreeView, QAbstractItemView, QSizePolicy, QHeaderView

from csvpath.util.nos import Nos
from csvpath.util.config import Config
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter

from flightpath.widgets.clickable_label import ClickableLabel
from flightpath.widgets.file_tree_model.treemodel import TreeModel
from flightpath.dialogs.new_run_dialog import NewRunDialog
from flightpath.dialogs.find_file_by_reference_dialog import FindFileByReferenceDialog

from .sidebar_file_ref_maker import SidebarFileRefMaker
from flightpath.util.help_finder import HelpFinder
from flightpath.widgets.help.plus_help import HelpHeaderView
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.message_utility import MessageUtility as meut

from flightpath.editable import EditStates
from .sidebar_right_base import SidebarRightBase

class SidebarNamedFiles(SidebarRightBase):

    def __init__(self, *, main, role=1, config:Config):
        super().__init__()
        self.role = role
        self.config = config
        self.setMinimumWidth(300)
        self.main = main
        self.view = None
        self.setup()

    def setup(self) -> None:
        try:
            layout = self.layout()
            if layout is None:
                layout = QVBoxLayout()
            layout.setSpacing(0)
            layout.setContentsMargins(1, 1, 1, 1)

            named_files_path = self.config.get(section="inputs", name="files")
            nos = Nos(named_files_path)
            try:
                if not nos.dir_exists():
                    #
                    #
                    #
                    nos.makedir()
            except Exception as ex:
                msg = f"Error during named-files inputs setup: {ex}"
                meut.warning(parent=self, msg=msg, title="Error")
                return

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
            self.model = TreeModel(headers=["Staged files"], data=nos, parent=self, title="Staged named-files", sidebar=self)
            self.model.set_style(self.view.style())
            self.view.setModel(self.model)
            #
            #
            #
            self.view.updateGeometries()
            layout.addWidget(self.view)
            self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.view.setContextMenuPolicy(Qt.CustomContextMenu)
            self.view.customContextMenuRequested.connect(self._show_context_menu)
            self._setup_view_context_menu()
            #
            #
            #
            self.view.setHeader(HelpHeaderView(self.view, on_help=self.main.helper.on_click_named_files_help))
            self.view.header().setSectionResizeMode(0, QHeaderView.Stretch)
            self.view.header().setFixedHeight(24)
            self.view.header().setStyleSheet("QHeaderView {font-size:13px}")
            #
            # moved from main
            #
            self.view.clicked.connect(self.on_named_file_tree_click)
            self.setLayout(layout)

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            print(f"error in named files: {type(e)}: {e}")
            meut.message(title=f"{type(e)} error loading named-files", msg=f"Named-files error: {e}")

    def update_style(self) -> None:
        try:
            self.model.set_style(self.view.style())
        except Exception as e:
            print(f"error in named files: {type(e)}: {e}")

    #
    # moved from main
    #
    def on_named_file_tree_click(self, index):
        self.main.selected_file_path = self.model.filePath(index)
        nos = Nos(self.main.selected_file_path)
        if not nos.isfile():
            ...
            #self._show_welcome_but_do_not_deselect()
        else:
            self.main.read_validate_and_display_file(editable=EditStates.UNEDITABLE)
            #self.main.read_validate_and_display_file(editable=EditStates.NO_SAVE_NO_CTX)
            self.main.statusBar().showMessage(f"  {self.main.selected_file_path}")

    def refresh(self) -> None:
        if self.view:
            layout = self.layout()  # Get the existing layout
            if layout:
                layout.removeWidget(self.view)
            self.view.deleteLater()  # Delete the old widget
            self.setup()

    def _setup_view_context_menu(self):
        self.context_menu = QMenu(self)
        # create actions
        self.new_run_action = QAction()
        self.new_run_action.setText("New run")
        self.new_run_action.triggered.connect(self._new_run)

        self.copy_path_action = QAction()
        self.copy_path_action.setText("Copy path")
        self.copy_path_action.triggered.connect(self._copy_path)

        self.find_data_action = QAction()
        self.find_data_action.setText("Find data")
        self.find_data_action.triggered.connect(self._find_data)

        self.delete_action = QAction()
        self.delete_action.setText("Permanent delete")
        self.delete_action.triggered.connect(self._delete_view_item)

        self.copy_action = QAction()
        self.copy_action.setText(self.tr("Copy to working dir"))
        self.copy_action.triggered.connect(self._copy_back_to_cwd)
        #self.copy_action.triggered.connect(self._copy_file_back_to_cwd)

        # setup callbacks
        # add to menu
        self.context_menu.addAction(self.new_run_action)
        self.context_menu.addAction(self.find_data_action)
        self.context_menu.addAction(self.copy_path_action)
        self.context_menu.addAction(self.copy_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.delete_action)

    def _show_context_menu(self, position):
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
                self.copy_path_action.setVisible(True)
                self.copy_action.setVisible(True)
                self.find_data_action.setVisible(True)
                self.delete_action.setVisible(False)
                self.new_run_action.setVisible(True)
            else:
                self.copy_path_action.setVisible(True)
                self.copy_action.setVisible(False)
                self.find_data_action.setVisible(True)
                self.delete_action.setVisible(True)
                self.new_run_action.setVisible(True)
            if path and ( path.endswith("manifest.json") or path.endswith(".db") ):
                self.copy_path_action.setVisible(False)
                self.copy_action.setVisible(True)
                self.find_data_action.setVisible(False)
                self.delete_action.setVisible(False)
                self.new_run_action.setVisible(False)
            if global_pos:
                self.context_menu.exec(global_pos)


    def _copy_path(self) -> None:
        from_index = self.view.currentIndex()
        if from_index.isValid():
            path = self.model.filePath(from_index)
            clipboard = QApplication.instance().clipboard()
            clipboard.setText(path)

    """
    def _copy_file_back_to_cwd(self) -> None:
        from_index = self.view.currentIndex()
        if from_index.isValid():
            from_path = self.model.filePath(from_index)
            to_index = self.main.sidebar.file_navigator.currentIndex()
            to_path = None
            if to_index.isValid():
                to_path = self.main.sidebar.proxy_model.filePath(to_index)
            else:
                to_path = self.main.state.cwd
            to_nos = Nos(to_path)
            if to_nos.isfile():
                to_nos.path = os.path.dirname(to_path)
            to_path = fiut.deconflicted_path(to_path, f"{os.path.basename(from_path)}")
            print(f"_copy_file_back_to_cwd: ")
            print(f"    from: {from_path}")
            print(f"      to: {to_path}")
            to_nos.path = to_path
            if to_nos.exists():
                #
                # this won't realistically happen
                #
                print(f"ERROR: {to_nos} exists")
            print(f"local path does not exist. ready to do the copy from {from_path}")
            print(f"doing the copy to {to_nos.path}")
            #
            # nos copy only works if we're copying to the same backend, which we won't always be.
            # so we use reader/writers. leaving as a reminder.
            #
            #from_nos.copy(to_nos.path)
            #
            try:
                with DataFileReader(from_path) as ffrom:
                    with DataFileWriter(path=to_path, mode="wb") as tto:
                        tto.write(ffrom.read())
            except NotADirectoryError:
                QMessageBox.warning(self, "Error", "Cannot copy item over another file")

        else:
            QMessageBox.warning(self, "Error", "Cannot copy item")
        """

    def _new_run(self):
        maker = SidebarFileRefMaker(parent=self, main=self.main)
        ref = maker.new_run_ref()
        self.new_run_dialog = NewRunDialog(parent=self, named_paths=None, named_file=ref)
        self.main.show_now_or_later(self.new_run_dialog)

    def _find_data(self):
        find = FindFileByReferenceDialog(main=self.main)
        self.main.show_now_or_later(find)

    def _delete_view_item(self):
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
                    self.window().statusBar().showMessage("{path} deleted")
                    #
                    # TODO: we recreate all the trees. very bad idea due to slow refresh from remote.
                    # but for now it should work. refreshing named_files is probably fair, but that's
                    # also tricky because we'd want to recreate the opened/closed state of the folders
                    # and if we did that the refresh might slow down potentially a lot. so long-term,
                    # seems like we should capture what is registered and manually add it. no fun. :/
                    #
                    #self.main._setup_central_widget()
                    self.main.renew_sidebar_named_files()




