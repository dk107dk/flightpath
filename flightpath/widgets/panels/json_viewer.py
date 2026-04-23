import os
import json
import tempfile
import traceback

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTreeView,
    QHeaderView,
    QSizePolicy,
    QMenu,
    QAbstractItemView,
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
from flightpath.util.message_utility import MessageUtility as meut
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.file_collector import FileCollector
from flightpath.util.editable import EditStates


class KeyableTreeView(QTreeView):
    def __init__(
        self,
        parent=None,
        *,
        key_callback=None,
        save_callback=None,
        editable=EditStates.EDITABLE,
    ):
        super().__init__(parent)
        try:
            self.key_callback = key_callback
            self.save_callback = save_callback
            self.editable = editable
            if self.save_callback and editable == EditStates.EDITABLE:
                save_shortcut_ctrl_save = QShortcut(QKeySequence("Ctrl+S"), self)
                save_shortcut_cmd_save = QShortcut(QKeySequence("Command+S"), self)
                save_shortcut_ctrl_save.activated.connect(self.save_callback)
                save_shortcut_cmd_save.activated.connect(self.save_callback)
            stut.set_editable_background(self)
        except Exception:
            print(traceback.format_exc())

    def keyPressEvent(self, event: QKeyEvent):
        if self.key_callback:
            self.key_callback(event)
        super().keyPressEvent(event)


class JsonViewer(QWidget):
    def __init__(
        self, *, main, editable=EditStates.EDITABLE, path: str = None, parent=None
    ):
        super().__init__(main if parent is None else parent)
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
        self._shown_no_edit_msg = None
        #
        # function is an optional indicator of what this view is showing. e.g. "variables" or
        # "errors". it is used to save back a viewer that is not backed by a file. when you
        # save, the data is serialized to a file that doesn't have a name and the user may not
        # have the opportunity to give one. in that case, if we have function, we'd use that
        # to create a reasonable name, e.g. "variables.json".
        #
        self.function = None
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
        self.view = KeyableTreeView(
            key_callback=self.key_click,
            save_callback=self._save,
            editable=self.editable,
        )
        self.content_view = self.view

        #
        # blocks double click to edit
        # we want to enable edit in some cases to make copying easier. but if we aren't explicitly editable
        # we must block saving.
        #
        if editable == EditStates.UNEDITABLE:
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
        # if self.editable == EditStates.EDITABLE:
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

    @property
    def function_name(self) -> str:
        if self.function is None or str(self.function).strip() == "":
            return "data.json"
        if self.function.endswith(".json"):
            return self.function
        return f"{self.function}.json"

    def on_double_click(self, index):
        if self.editable == EditStates.UNEDITABLE:
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
            if self.editable == EditStates.NO_SAVE_NO_CTX:
                if self._shown_no_edit_msg is None:
                    meut.message(
                        parent=self,
                        title="Not Editable",
                        msg="This file is not editable. Any changes you make will be discarded.",
                    )
                    self._shown_no_edit_msg = True
                # we can let them edit, but not save
                return
            #
            # open a file dialog to find csvpaths
            #
            path = FileCollector.select_file(
                parent=self,
                cwd=self.main.state.cwd,
                title="Please pick a csvpath to add",
                file_type_filter=FileCollector.csvpaths_filter(
                    self.main.csvpath_config
                ),
            )
            item.value = path

    def _set_modified(self, t: bool) -> None:
        if self.editable == EditStates.NO_SAVE_NO_CTX:
            self.modified = False
            return
        self.modified = t
        tab = taut.find_tab(self.main.content.tab_widget, self.path)
        if tab is None:
            return
        name = (
            f"+ {os.path.basename(self.path)}"
            if t is True
            else os.path.basename(self.path)
        )
        self.main.content.tab_widget.setTabText(tab[0], name)

    def key_click(self, event):
        if self.editable == EditStates.UNEDITABLE:
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

    def _copy_back_question(self) -> None:
        print(f"cpbm question: parent: {self.parent()}")
        yes = meut.yesNo(
            parent=self.main.helper.help_and_feedback,
            msg="You can't edit here. Copy back to project?",
            title="Copy file to project?",
        )
        print(f"cpbm question: yes: {yes}")
        if yes is True:
            try:
                name = self.objectName()
                if not name or str(name).strip() == "":
                    #
                    # we're probably a vars or errors results tab with no file backing us up
                    #
                    with tempfile.NamedTemporaryFile(
                        mode="w", delete=True, suffix=".json"
                    ) as file:
                        _data = json.dumps(self.model.to_json(), indent=2)
                        file.write(_data)
                        file.flush()
                        to_path = fiut.copy_results_back_to_cwd(
                            main=self.main,
                            from_path=file.name,
                            use_name=self.function_name,
                        )
                        self.main.read_validate_and_display_file_for_path(to_path)
                        #
                        # no tab to close
                        # self.main.content.tab_widget.close_tab(name)
                elif name.endswith(".tracking"):
                    #
                    # this is a turn-by-turn metadata from an AI request. i'm not convinced we
                    # don't want to handle .tracking files differently so putting it in its own
                    # place.
                    #
                    with tempfile.NamedTemporaryFile(
                        mode="w", delete=True, suffix=".json"
                    ) as file:
                        _data = json.dumps(self.model.to_json(), indent=2)
                        file.write(_data)
                        file.flush()
                        to_path = fiut.copy_results_back_to_cwd(
                            main=self.main,
                            from_path=file.name,
                            use_name=f"{name}.json",
                        )
                        print(f"jsonver: doing redcva for path: {to_path}")
                        self.main.read_validate_and_display_file_for_path(to_path)
                        print(
                            f"jsonver: done doing redcva for path: {to_path}. should be open."
                        )
                else:
                    print(f"cpbm question: name: {name}")
                    to_path = fiut.copy_results_back_to_cwd(
                        main=self.main, from_path=name
                    )
                    print("cpbm question: fiut done")
                    self.main.read_validate_and_display_file_for_path(to_path)
                    print("cpbm question: main.read done")
                    self.main.content.tab_widget.close_tab(name)
                    print("cpbm question: done")
            except Exception:
                print(traceback.format_exc())

    def _show_context_menu(self, position):
        if self.editable == EditStates.UNEDITABLE:
            #
            # if we aren't editable we need to ask the user if they want to copy back to the project.
            #
            print("before ocpyback quest")
            self._copy_back_question()
            print("after ocpyback quest")
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
        if self.editable == EditStates.UNEDITABLE:
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
        #
        # make the doc modified
        #
        self._set_modified(True)

    def _add_named_paths(self) -> None:
        invalid = self.context_menu_invalid
        index = self.view.currentIndex()
        parent = self.model.root if invalid else index.internalPointer()
        PickPathsDialog(main=self.main, tree=self.model, parent_item=parent)
        self._set_modified(True)

    def _add_csvpath(self) -> None:
        index = self.view.currentIndex()
        parent = index.internalPointer()
        path = FileCollector.select_file(
            parent=self,
            cwd=self.main.state.cwd,
            title="Please pick a csvpath to add",
            file_type_filter=FileCollector.csvpaths_filter(self.main.csvpath_config),
        )
        self.model.beginResetModel()
        item = TreeItem(parent)
        item.key = parent.childCount()
        item.value = path
        item.value_type = type(str)
        parent.appendChild(item)
        self.model.endResetModel()
        self._set_modified(True)

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
        self._set_modified(True)

    def _add_other(self) -> None:
        index = self.view.currentIndex()
        parent = index.internalPointer()
        AddConfigKeyDialog(main=self.main, tree=self.model, parent_item=parent)
        self._set_modified(True)

    def _delete_item(self) -> None:
        index = self.view.currentIndex()
        self.model.remove(index)
        self._set_modified(True)

    def open_file(self, *, path: str, data: str):
        if path:
            self.path = path
        #
        # do we really want / need to double check if we're handling a file?
        #
        if path and (Nos(path).isfile() is False or QFileInfo(path).suffix() != "json"):
            self.view.hide()
            return
        _ = json.loads(data)
        self.model.load(_)
        self.main.show_now_or_later(self.view)
        self.view.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.view.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.view.setAlternatingRowColors(True)

    def clear(self):
        self.view.hide()
