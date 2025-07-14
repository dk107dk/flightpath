import sys
import os
import json
import re
from pathlib import Path

from PySide6.QtWidgets import (
    QPushButton,
    QWidget,
    QComboBox,
    QMenu,
    QMessageBox,
    QVBoxLayout
)

from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QSize, QModelIndex
from PySide6.QtWidgets import QTreeView, QAbstractItemView, QSizePolicy, QHeaderView

from csvpath.util.nos import Nos
from csvpath.util.config import Config
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter

from flightpath.widgets.clickable_label import ClickableLabel
from flightpath.widgets.file_tree_model.treemodel import TreeModel
from flightpath.widgets.help.plus_help import HelpHeaderView
from flightpath.util.file_utility import FileUtility as fiut
from .sidebar_archive_ref_maker import SidebarArchiveRefMaker
from flightpath.dialogs.find_file_by_reference_dialog import FindFileByReferenceDialog
from flightpath.util.message_utility import MessageUtility as meut

from flightpath.editable import EditStates

class SidebarArchive(QWidget):

    def __init__(self, *, role=1, main, config:Config):
        super().__init__()
        self.role = role
        self.main = main
        self.config = config
        self.setMinimumWidth(300)
        self.context_menu = None
        self.view = None
        self.model = None
        self.setup()

    def setup(self) -> None:
        try:
            layout = self.layout()
            if layout is None:
                layout = QVBoxLayout()
            layout.setSpacing(0)
            layout.setContentsMargins(1, 1, 1, 1)

            archive_path = self.config.get(section="results", name="archive")
            nos = Nos(archive_path)
            if not nos.dir_exists():
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
            self.model = TreeModel(["Archive"], nos, self, title="Archived results", sidebar=self)
            self.model.set_style(self.view.style())
            self.view.setModel(self.model)
            self.view.updateGeometries()

            layout.addWidget(self.view)
            #
            #
            #
            self.view.setHeader(HelpHeaderView(self.view, on_help=self.main.helper.on_click_archive_help))
            self.view.header().setSectionResizeMode(0, QHeaderView.Stretch)
            self.view.header().setFixedHeight(24)
            self.view.header().setStyleSheet("QHeaderView {font-size:13px}")
            #
            #
            #
            #
            # set up context menu
            #
            self.view.setContextMenuPolicy(Qt.CustomContextMenu)
            self.view.customContextMenuRequested.connect(self._show_context_menu)
            self._setup_view_context_menu()
            #
            # moved from main
            #
            self.view.clicked.connect(self.on_archive_tree_click)
            self.setLayout(layout)
        except Exception as e:
            meut.message(title=f"{type(e)} error loading named-paths", msg=f"Archive error: {e}")

    #
    # moved from main
    #
    def on_archive_tree_click(self, index):
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
            print(f"{type(e)} error in archive: {e}")

    def refresh(self) -> None:
        if self.view:
            layout = self.layout()  # Get the existing layout
            layout.removeWidget(self.view)
            self.view.deleteLater()  # Delete the old widget
            self.setup()

    #
    # actions support
    #

    def _setup_view_context_menu(self):
        self.context_menu = QMenu(self)

        self.new_run_action = QAction()
        self.new_run_action.setText(self.tr("New run"))
        self.new_run_action.triggered.connect(self._new_run)

        self.repeat_run_action = QAction()
        self.repeat_run_action.setText(self.tr("Repeat run"))
        self.repeat_run_action.triggered.connect(self._repeat_run)

        self.find_data_action = QAction()
        self.find_data_action.setText("Find data")
        self.find_data_action.triggered.connect(self._find_data)

        self.copy_action = QAction()
        self.copy_action.setText(self.tr("Copy to working dir"))
        self.copy_action.triggered.connect(self._copy_results_back_to_cwd)

        self.delete_action = QAction()
        self.delete_action.setText(self.tr("Permanent delete"))
        self.delete_action.triggered.connect(self._delete_file_navigator_item)

        self.context_menu.addAction(self.repeat_run_action)
        self.context_menu.addAction(self.new_run_action)
        self.context_menu.addAction(self.find_data_action)
        self.context_menu.addAction(self.copy_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.delete_action)

    def _show_context_menu(self, position):
        index = self.view.indexAt(position)
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
                self.new_run_action.setVisible(True)
                self.repeat_run_action.setVisible(True)
                self.find_data_action.setVisible(True)
                self.copy_action.setVisible(True)
            else:
                self.delete_action.setVisible(True)
                self.new_run_action.setVisible(True)
                self.repeat_run_action.setVisible(True)
                self.find_data_action.setVisible(True)
                self.copy_action.setVisible(False)
        if path.endswith("manifest.json") or path.endswith(".db"):
            # we don't allow anything on manifests or sqlite files
            ...
        else:
            self.context_menu.exec(global_pos)

    def _find_data(self):
        find = FindFileByReferenceDialog(main=self.main)
        self.main.show_now_or_later(find)

    def _copy_results_back_to_cwd(self) -> None:
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
                to_nos.path = os.path.dirname(to_path)
            to_path = fiut.deconflicted_path(to_path, f"{os.path.basename(from_path)}")
            to_nos.path = to_path
            if to_nos.exists():
                #
                # this won't realistically happen
                #
                print(f"ERROR: {to_nos} exists")
            #from_nos.copy(to_nos.path)
            with DataFileReader(from_path) as ffrom:
                with DataFileWriter(path=to_path) as tto:
                    tto.write(ffrom.read())

        else:
            QMessageBox.warning(self, "Error", "Cannot copy item")

    def _new_run(self) -> None:
        maker = SidebarArchiveRefMaker(main=self.main, parent=self)
        maker._new_run()

    def _repeat_run(self) -> None:
        maker = SidebarArchiveRefMaker(main=self.main, parent=self)
        maker._repeat_run()

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
                    QMessageBox.warning(self, "Error", str(e))
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
                    self.main.renew_sidebar_archive()
                    #
                    # do we reset the connects for on click?
                    #
                    # _connects -> on_archive_tree_click -> read_validate_and_display_file
                    #
                    #   self.sidebar_rt_bottom.view.clicked.connect(self.on_archive_tree_click)
                    #
                    #


