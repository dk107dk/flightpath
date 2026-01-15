import sys
import os
import json
from typing import Any

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
from csvpath.util.file_readers import DataFileReader
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
from flightpath.editable import EditStates

from flightpath.widgets.editor.editor import Editor
from flightpath.util.string_utility import StringUtility as strut



class JsonViewer2(QWidget):

    def __init__(self, main, editable=EditStates.EDITABLE, path:str=None):
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
        self._shown_no_edit_msg = None
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
        self.view = Editor(parent=self, editable=self.editable)
        #
        # blocks double click to edit
        # we want to enable edit in some cases to make copying easier. but if we aren't explicitly editable
        # we must block saving.
        #
        if editable == EditStates.UNEDITABLE:
            #self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)
            ...
        #
        #
        #
        save_shortcut_ctrl_save = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut_cmd_save = QShortcut(QKeySequence("Command+S"), self)
        save_shortcut_ctrl_save.activated.connect(self._save)
        save_shortcut_cmd_save.activated.connect(self._save)

        self.context_menu = None
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self._show_context_menu)
        self._setup_view_context_menu()
        #
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



    def _set_modified(self, t:bool) -> None:
        if self.editable == EditStates.NO_SAVE_NO_CTX:
            self.modified = False
            return
        self.modified = t
        tab = taut.find_tab(self.main.content.tab_widget, self.path)
        if tab is None:
            return
        name = f"+ {os.path.basename(self.path)}" if t is True else os.path.basename(self.path)
        self.main.content.tab_widget.setTabText( tab[0], name)

    def _setup_view_context_menu(self):
        self.context_menu = QMenu(self)
        self.save_action = QAction()
        self.save_action.setText("Save")
        self.save_action.triggered.connect(self._save)
        self.context_menu.addAction(self.save_action)

        self.well_formed_action = QAction()
        self.well_formed_action.setText("Check well-formedness")
        self.well_formed_action.triggered.connect(self._check)
        self.context_menu.addAction(self.well_formed_action)

        self.pretty_print_action = QAction()
        self.pretty_print_action.setText("Pretty print")
        self.pretty_print_action.triggered.connect(self._pretty)
        self.context_menu.addAction(self.pretty_print_action)

    def _copy_back_question(self) -> None:
        yes = meut.yesNo( parent=self, msg="You can't edit here. Copy back to project?", title="Copy file to project?")
        if yes is True:
            try:
                name = self.objectName()
                to_path = fiut.copy_results_back_to_cwd(main=self.main, from_path=name)
                self.main.read_validate_and_display_file_for_path(to_path)
                self.main.content.tab_widget.close_tab(name)
            except Exception:
                import traceback
                print(traceback.format_exc())

    def _show_context_menu(self, position):
        if self.editable == EditStates.UNEDITABLE:
            #
            # if we aren't editable we need to ask the user if they want to copy back to the project.
            #
            self._copy_back_question()
            return
        global_pos = self.view.viewport().mapToGlobal(position)

        if self.modified:
            self.save_action.setEnabled(True)
        else:
            self.save_action.setEnabled(False)

        self.context_menu.exec(global_pos)

    def _save(self) -> None:
        if self.editable == EditStates.UNEDITABLE:
            return
        if self.path is None:
            print("Error: cannot save json to file path None")
            return
        t = self.view.toPlainText()
        t = strut.sanitize_json(t)

        info = QFileInfo(self.path)
        if info.suffix() in ["jsonl", "ndjson", "jsonlines"]:
            try:
                #
                # this could be slow for large files due to how we find the
                # lines. we can not pretty print here to speed things up; instead
                # making the user actively ask for pretty printing. still, that
                # wouldn't fix the performance problem, only minimize it. before
                # creating a real parser let's see if there are complaints. or
                # maybe there's a jsonl formatter that I just didn't find?
                #
                t = strut.jsonl_text_to_lines(t)
            except:
                ...
        else:
            try:
                j = json.loads(t)
                t = json.dumps(j, indent=2)
            except:
                #
                # would be good to notify the user here
                #
                print(f"cannot format as json")
        with DataFileWriter(path=self.path) as file:
            file.write(t)
        #
        # reset the name w/o the +
        #
        self._set_modified(False)

    def _pretty(self) -> str:
        info = QFileInfo(self.path)
        #
        # do we really want / need to double check if we're handling a file?
        #
        t = None
        if info.suffix() in ["jsonl", "ndjson", "jsonlines"]:
            t = strut.jsonl_text_to_lines(self.view.toPlainText())
        else:
            t = self._check(show_good_message=False)
        self.view.setPlainText(t)

    def _check(self, *, show_good_message=True) -> str:
        t = self.view.toPlainText()
        t1 = strut.sanitize_json(t)
        try:
            j = json.loads(t1)
            t1 = json.dumps(j, indent=2)
        except json.decoder.JSONDecodeError as e:
            self._formatting_error(t, e)
            return t
        if show_good_message is True:
            meut.message(msg="This file is well-formed JSON", title="Well-formed")
        return t1

    def _formatting_error(self, t:str, e) -> None:
        #
        # t is the original text
        #
        msg = None
        line, line_char = self._error_location(t, e)
        if line is not None and line_char is not None:
            msg = f"Error in JSON format at line {line+1}, char {line_char+1}\n\nOriginal error: {e}"
        else:
            msg = f"Error in format.\n\nOriginal error messsage: {e}"
        meut.warning(parent=self, msg=msg, title="Malformed JSON")

    def _error_location(self, t:str, e) -> tuple[int, int]:
        print(f"serloc: {e}")
        try:
            estr = f"{e}"
            if estr.find("line "):
                s = t.split("\n")
                line = 0
                ffrom = estr.rfind("(") + 1
                to = estr.rfind(")")
                char = estr[ffrom+5:to]
                print(f"char: char")
                char = int(char)
                line = 0
                line_char = 0
                for i, c in enumerate(t):
                    line_char += 1
                    if c == '\n':
                        line += 1
                        line_char = 1
                    elif i == char:
                        break
                print(f"serloc 2: {ffrom}, {to}, {char}, {line}, {line_char}")
                return line, line_char
        except Exception as ex:
            print(f"serloc 3: {ex}")
            ...
        return None, None

    def open_file(self, *, path:str, data:str):
        #
        # we still want the data for the old grid view, but here we just want the
        # string. <<< means we're loading twice. that can't be right.
        #
        self.path = path
        info = QFileInfo(path)
        #
        # do we really want / need to double check if we're handling a file?
        #
        nos = Nos(path)
        if not nos.isfile() or info.suffix() not in ["json", "jsonl", "ndjson", "jsonlines"]:
            self.view.hide()
            #
            # need an alert here
            #
            meut.warning(parent=self.main, msg="Unknown file type", title="Cannot open file")
            return
        t = data
        if t is None or not isinstance(t, str):
            with DataFileReader(path) as file:
                t = file.read()
        if not nos.isfile() or info.suffix() not in ["jsonl", "ndjson", "jsonlines"]:
            try:
                j = json.loads(t)
                t = json.dumps(j, indent=2)
            except:
                #
                # would be good to notify the user here?
                #  assuming there is any data to fail to format.
                #
                print(f"cannot format {path} as json")
        self.view.setPlainText(t)
        self.main.show_now_or_later(self.view)

    def clear(self):
        self.view.hide()



    #
    # the below are from json and data viewer classes.
    #not sure why we need them here yet.
    # we only need them if we could be in json_viewer_2 and someone clicks the node so that it
    # wants to open in data_viewer or json_viewer.
    #
    # we want that to never happen. we have to close and reopen the file if it is in the wrong viewer
    #
    # remove
    #
    def display_data(self, model):
        """
        self.table_view.setModel(model)
        self.main.show_now_or_later(self.table_view)
        self.main.show_now_or_later(self.parent.toolbar)
        self.layout().setCurrentIndex(0)
        """

    #
    # remove
    #
    #@Slot(tuple)
    def on_row_or_column_edit(self, fromf:tuple[int,int]) -> None:
        """
        self.mark_unsaved()
        """

    #
    # remove
    #
    #@Slot(tuple)
    def on_edit_made(self, xy:tuple[int,int, Any, Any]) -> None:
        """
        if xy[2] != xy[3]:
            self.mark_unsaved()
            #
            # other actions?
            #
        """
