import sys
import os
import json

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTreeView,
    QHeaderView,
    QSizePolicy,
    QMenu,
    QAbstractItemView

)
from PySide6.QtCore import Qt, QFileInfo
from PySide6.QtGui import QAction, QKeyEvent, QShortcut, QKeySequence

from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos

from flightpath.widgets.json_tree_model.json_model import JsonModel
from flightpath.dialogs.pick_paths_dialog import PickPathsDialog
from flightpath.dialogs.add_config_key_dialog import AddConfigKeyDialog
from flightpath.widgets.json_tree_model.json_tree_item import TreeItem
from flightpath.util.tabs_utility import TabsUtility as taut
from flightpath.util.style_utils import StyleUtility as stut
from flightpath.util.file_collector import FileCollector

class KeyableTreeView(QTreeView):

    def __init__(self, parent=None, *, key_callback=None, save_callback=None, editable=True):
        super().__init__(parent)
        self.key_callback = key_callback
        self.save_callback = save_callback
        self.editable = editable
        if self.save_callback and editable:
            save_shortcut_ctrl_save = QShortcut(QKeySequence("Ctrl+S"), self)
            save_shortcut_cmd_save = QShortcut(QKeySequence("Command+S"), self)
            save_shortcut_ctrl_save.activated.connect(self.save_callback)
            save_shortcut_cmd_save.activated.connect(self.save_callback)

    def keyPressEvent(self, event: QKeyEvent):
        if self.key_callback:
            self.key_callback(event)
        super().keyPressEvent(event)


class JsonViewer(QWidget):

    def __init__(self, main, editable=True, path:str=None):
        super().__init__()
        #
        # for a left-hand side file the path cannot be None. we need to know
        # where to save the data. a right-hand side file can be none. we need
        # to know that we cannot edit or save. in that case, the file needs to
        # be copied back to the cwd for editing.
        #
        # this value can / is also set in open_file() below
        #
        self.path = None
        self.main = main
        self.editable = editable
        #
        # sets the font size
        #
        stut.set_common_style(self)
        #
        #
        #
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.view = KeyableTreeView(key_callback=self.key_click, save_callback=self._save, editable=editable)
        #
        # blocks double click to edit
        #
        if editable is False:
            self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        #
        #
        #
        self.model = JsonModel()
        self.view.setModel(self.model)
        #
        #
        #
        self.context_menu = None
        if self.editable:
            self.view.setContextMenuPolicy(Qt.CustomContextMenu)
            self.view.customContextMenuRequested.connect(self._show_context_menu)
            self._setup_view_context_menu()
        #
        # catch attempts to edit
        #
        self.view.doubleClicked.connect(self.on_double_click)
        layout.addWidget(self.view)
        #
        # if invalid -- click was off the tree -- we set this so that
        # we can take advantage when the user selects from the menu.
        # the reason is that we apparently have invalidity at the point
        # we catch the click but seems to be valid in every case when
        # we select from the menu. which sort of makes sense.
        #
        self.context_menu_invalid = True
        #
        # set to True when the file has changed and needs to be saved
        #
        self.modified = False


    def on_double_click(self, index):
        if not self.editable:
            return
        item = index.internalPointer()
        if not index.isValid():
            return
        path = self.model.item_path(item)
        if len(path) == 2:
            # no reason to double click on config or the named-paths
            return
        if len(path) == 3:
            if path[1] == "_config":
                # just edit
                return
            #
            # open a file dialog to find csvpaths
            #
            path = FileCollector.select_file(
                parent=self,
                cwd=self.main.state.cwd,
                title="Please pick a csvpath to add",
                file_type_filter=FileCollector.csvpaths_filter(self.main.csvpath_config)
            )
            item.value = path

    def _set_modified(self, t:bool) -> None:
        self.modified = t
        tab = taut.find_tab(self.main.content.tab_widget, self.path)
        if tab is None:
            print(f"Error: cannot find view tab in main.content for {self.path}")
            return
        name = f"+ {os.path.basename(self.path)}" if t is True else os.path.basename(self.path)
        self.main.content.tab_widget.setTabText( tab[0], name)

    def key_click(self, event):
        if not self.editable:
            return
        if event.key() in [Qt.Key_Down, Qt.Key_Up, Qt.Key_Left, Qt.Key_Right]:
            ...
        else:
            self._set_modified(True)
        super().keyPressEvent(event)


    def _setup_view_context_menu(self):
        self.context_menu = QMenu(self)

        self.add_config_action = QAction()
        self.add_config_action.setText("Add config section")
        self.add_config_action.triggered.connect(self._add_config)
        self.context_menu.addAction(self.add_config_action)

        self.add_named_paths_action = QAction()
        self.add_named_paths_action.setText("Add named-paths group")
        self.add_named_paths_action.triggered.connect(self._add_named_paths)
        self.context_menu.addAction(self.add_named_paths_action)

        self.add_csvpath_action = QAction()
        self.add_csvpath_action.setText("Add a csvpath file")
        self.add_csvpath_action.triggered.connect(self._add_csvpath)
        self.context_menu.addAction(self.add_csvpath_action)

        self.add_template_action = QAction()
        self.add_template_action.setText("Add template")
        self.add_template_action.triggered.connect(self._add_template)
        self.context_menu.addAction(self.add_template_action)

        self.add_other_action = QAction()
        self.add_other_action.setText("Add other config data")
        self.add_other_action.triggered.connect(self._add_other)
        self.context_menu.addAction(self.add_other_action)

        self.context_menu.addSeparator()

        self.delete_item_action = QAction()
        self.delete_item_action.setText("Delete this")
        self.delete_item_action.triggered.connect(self._delete_item)
        self.context_menu.addAction(self.delete_item_action)

        self.context_menu.addSeparator()

        self.save_action = QAction()
        self.save_action.setText("Save")
        self.save_action.triggered.connect(self._save)
        self.context_menu.addAction(self.save_action)

    def _show_context_menu(self, position):
        if not self.editable:
            return
        index = self.view.indexAt(position)
        global_pos = self.view.viewport().mapToGlobal(position)
        if index.isValid():
            self.context_menu_invalid = False
            item = index.internalPointer()
            self._setup_for_config_if(item)
            self._setup_for_config_named_paths_if(item)
            self._setup_for_named_paths_if(item)
            # this parent parent is a sweeper that fixes for at least one of the above
            self._setup_for_parent_parent(item)
            self.delete_item_action.setEnabled(True)
        else:
            self.context_menu_invalid = True
            #
            # config only enabled if we don't already have one
            #
            if self._has_config():
                self.add_config_action.setEnabled(False)
            else:
                self.add_config_action.setEnabled(True)
            self.add_named_paths_action.setEnabled(True)
            # falses
            self.add_template_action.setEnabled(False)
            self.add_other_action.setEnabled(False)
            self.add_csvpath_action.setEnabled(False)
            self.delete_item_action.setEnabled(False)
        if self.modified:
            self.save_action.setEnabled(True)
        else:
            self.save_action.setEnabled(False)
        self.context_menu.exec(global_pos)

    def _setup_for_parent_parent(self, item):
        if (
            item.parent.parent
            and item.parent.parent.key in ["root", "_config"]
            and item.parent.key != "_config"
        ):
            self.add_template_action.setEnabled(False)
            self.add_other_action.setEnabled(False)
            self.add_named_paths_action.setEnabled(False)
            self.add_csvpath_action.setEnabled(False)
            self.add_config_action.setEnabled(False)

    def _setup_for_config_if(self, item):
        if item.key == "_config":
            self.add_named_paths_action.setEnabled(True)
            # falses
            self.add_csvpath_action.setEnabled(False)
            self.add_template_action.setEnabled(False)
            self.add_other_action.setEnabled(False)
            self.add_config_action.setEnabled(False)

    def _setup_for_config_named_paths_if(self, item):
        if item.parent.key == "_config":
            if self._has_template(item):
                self.add_template_action.setEnabled(False)
            else:
                self.add_template_action.setEnabled(True)
            self.add_other_action.setEnabled(True)
            # falses
            self.add_named_paths_action.setEnabled(False)
            self.add_config_action.setEnabled(False)
            self.add_csvpath_action.setEnabled(False)

    def _setup_for_named_paths_if(self, item):
        if item.parent.key == "root" and item.key != "_config":
            self.add_csvpath_action.setEnabled(True)
            # falses
            self.add_template_action.setEnabled(False)
            self.add_other_action.setEnabled(False)
            self.add_named_paths_action.setEnabled(False)

    def _has_template(self, item) -> bool:
        for c in item.children:
            if c.key == "template":
                return True
        return False

    def _has_config(self) -> bool:
        for c in self.model.root.children:
            if c.key == "_config":
                return True
        return False

    def _save(self) -> None:
        if not self.editable:
            return
        if self.path is None:
            print("Error: cannot save json to file path None")
            return
        d = self.model.to_json()
        j = json.dumps(d, indent=2)
        with DataFileWriter(path=self.path) as file:
            file.write(j)
        #
        # reset the name w/o the +
        #
        self._set_modified(False)

    def _add_config(self) -> None:
        invalid = self.context_menu_invalid
        if not invalid:
            # shouldn't happen
            return
        parent = self.model.root
        self.model.beginResetModel()
        item = TreeItem(parent)
        item.key = "_config"
        item.value_type = type({})
        parent.appendChild(item)
        self.model.endResetModel()

    def _add_named_paths(self) -> None:
        invalid = self.context_menu_invalid
        index = self.view.currentIndex()
        parent = self.model.root if invalid else index.internalPointer()
        PickPathsDialog(main=self.main, tree=self.model, parent_item=parent)

    def _add_csvpath(self) -> None:
        index = self.view.currentIndex()
        parent = index.internalPointer()
        path = FileCollector.select_file(
            parent=self,
            cwd=self.main.state.cwd,
            title="Please pick a csvpath to add",
            file_type_filter=FileCollector.csvpaths_filter(self.main.csvpath_config)
        )
        self.model.beginResetModel()
        item = TreeItem(parent)
        item.key = parent.childCount()
        item.value = path
        item.value_type = type(str)
        parent.appendChild(item)
        self.model.endResetModel()

    def _add_template(self) -> None:
        index = self.view.currentIndex()
        parent = index.internalPointer()
        self.model.beginResetModel()
        item = TreeItem(parent)
        item.key = "template"
        item.value = ""
        item.value_type = type("")
        parent.appendChild(item)
        self.model.endResetModel()

    def _add_other(self) -> None:
        index = self.view.currentIndex()
        parent = index.internalPointer()
        AddConfigKeyDialog(main=self.main, tree=self.model, parent_item=parent)

    def _delete_item(self) -> None:
        index = self.view.currentIndex()
        item = index.internalPointer()
        self.model.remove(index)

    def open_file(self, *, path:str, data:str):
        self.path = path
        info = QFileInfo(path)
        #
        # do we really want / need to double check if we're handling a file?
        #
        nos = Nos(path)
        if not nos.isfile() or info.suffix() != "json":
            self.view.hide()
            return
        self.model.load(data)
        self.view.show()
        self.view.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.view.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.view.setAlternatingRowColors(True)

    def clear(self):
        self.view.hide()



