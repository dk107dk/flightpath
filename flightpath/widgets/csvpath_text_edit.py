import os
from PySide6.QtWidgets import QPlainTextEdit, QStyle, QMenu
from PySide6.QtGui import QAction, QKeyEvent, QKeySequence, QShortcut, QPixmap, QPainter, QIcon, QFont
from PySide6.QtCore import Qt
from PySide6.QtSvg import QSvgRenderer

from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos
from csvpath.managers.paths.paths_manager import PathsManager

from flightpath.util.csvpath_loader import CsvpathLoader
from flightpath.util.message_utility import MessageUtility as meut
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.syntax.span_utility import SpanUtility as sput
from flightpath.util.os_utility import OsUtility as osut
from flightpath.util.syntax.csvpath_highlighter import CsvPathSyntaxHighlighter
from flightpath.dialogs.generate_csv_dialog import GenerateCsvDialog
from flightpath.dialogs.ask_question_dialog import AskQuestionDialog

from flightpath.editable import EditStates

class CsvPathTextEdit(QPlainTextEdit):

    def __init__(self, *, main, parent, editable=EditStates.EDITABLE) -> None:
        super().__init__()
        self.main = main
        self.parent = parent
        self.editable = editable
        self.icon = None
        self.parent.saved = True
        #
        #
        #
        save_shortcut_ctrl = QShortcut(QKeySequence("Ctrl+s"), self)
        save_shortcut_ctrl.activated.connect(self.on_save)
        save_shortcut_ctrl = QShortcut(QKeySequence("Shift+Ctrl+S"), self)
        save_shortcut_ctrl.activated.connect(self.on_save_as)
        #
        #
        #
        run_shortcut_ctrl = QShortcut(QKeySequence("Ctrl+r"), self)
        run_shortcut_ctrl.activated.connect(self.on_run)
        #
        #
        #
        load_shortcut_ctrl = QShortcut(QKeySequence("Ctrl+l"), self)
        load_shortcut_ctrl.activated.connect(self.on_load)
        #
        #
        #
        append_shortcut_ctrl = QShortcut(QKeySequence("Shift+Ctrl+A"), self)
        append_shortcut_ctrl.activated.connect(self.on_append)
        #
        #
        #
        generate_shortcut_ctrl = QShortcut(QKeySequence("Shift+Ctrl+G"), self)
        generate_shortcut_ctrl.activated.connect(self.on_generate_data)

        ask_question_ctrl = QShortcut(QKeySequence("Shift+Ctrl+Q"), self)
        ask_question_ctrl.activated.connect(self.on_ask_question)

        self.load_dialog = None

    def keyPressEvent(self, event: QKeyEvent):
        if self.editable == EditStates.UNEDITABLE:
            return
        super().keyPressEvent(event)
        t = event.text()
        #
        # not sure why t would exist but be ""
        #
        #if t and t != "":
        self.desaved()

    def desaved(self) -> bool:
        if self.editable == EditStates.UNEDITABLE:
            return False
        if self.parent.saved is True:
            path = self.parent.path
            path = os.path.dirname(path)
            i = self.main.content.tab_widget.currentIndex()
            name = self.main.content.tab_widget.tabText(i)
            name = name.replace("+", "")
            name = name.strip()
            self.main.content.tab_widget.setTabText(i, f"+ {name}" )
            self.main.statusBar().showMessage(f"{path}{os.sep}{name}+")
            self.parent.saved = False
        return True

    def background_changed(self) -> None:
        CsvPathSyntaxHighlighter(self.document())

    def contextMenuEvent(self, event):
        if self.editable == EditStates.UNEDITABLE:
            self._copy_back_question()
            return
        menu = self.createStandardContextMenu()

        #
        # several actions are default, but qt doesn't add shortcuts
        #
        for action in menu.actions():
            if isinstance(action, QAction):
                t = action.text()
                if t and str(t).strip() != "":
                    t = t.replace("&", "").lower()
                    if t == "cut":
                        action.setShortcut(QKeySequence("Ctrl+x"))
                    if t == "copy":
                        action.setShortcut(QKeySequence("Ctrl+c"))
                    if t == "paste":
                        action.setShortcut(QKeySequence("Ctrl+v"))
                    if t == "undo":
                        action.setShortcut(QKeySequence("Ctrl+z"))
                    if t == "redo":
                        action.setShortcut(QKeySequence("Shift+Ctrl+Z"))
                    if "select" in t:
                        action.setShortcut(QKeySequence("Ctrl+a"))
                    if t == "delete":
                        action.setShortcut(QKeySequence("Ctrl+d"))
                    action.setShortcutVisibleInContextMenu(True)

        #
        # separator and save options
        #
        menu.addSeparator()
        save = "Save"
        save_action = QAction(save, self)
        save_action.triggered.connect(self.on_save)
        save_action.setShortcut(QKeySequence("Ctrl+s"))
        save_action.setShortcutVisibleInContextMenu(True)
        menu.addAction(save_action)

        save_as_action = QAction("Save as", self)
        save_as_action.setShortcut(QKeySequence("Shift+Ctrl+S"))
        save_as_action.setShortcutVisibleInContextMenu(True)
        save_as_action.triggered.connect(self.on_save_as)
        menu.addAction(save_as_action)
        #
        # separator and run
        #
        menu.addSeparator()
        load_action = QAction("Load to group", self)
        load_action.triggered.connect(self.on_load)
        load_action.setShortcut(QKeySequence("Ctrl+l"))
        load_action.setShortcutVisibleInContextMenu(True)
        menu.addAction(load_action)
        #
        # separator and run
        #
        #menu.addSeparator()
        run_action = QAction("Run", self)
        run_action.triggered.connect(self.on_run)
        run_action.setShortcut(QKeySequence("Ctrl+r"))
        run_action.setShortcutVisibleInContextMenu(True)
        menu.addAction(run_action)

        menu.addSeparator()
        append_action = QAction("Append a csvpath", self)
        append_action.triggered.connect(self.on_append)
        append_action.setShortcut(QKeySequence("Shift+Ctrl+A"))
        append_action.setShortcutVisibleInContextMenu(True)
        menu.addAction(append_action)

        menu.addSeparator()
        generate_data_action = QAction("Generate data", self)
        generate_data_action.triggered.connect(self.on_generate_data)
        generate_data_action.setShortcut(QKeySequence("Shift+Ctrl+G"))
        generate_data_action.setShortcutVisibleInContextMenu(True)
        menu.addAction(generate_data_action)

        ask_question_action = QAction("Ask question", self)
        ask_question_action.triggered.connect(self.on_ask_question)
        ask_question_action.setShortcut(QKeySequence("Shift+Ctrl+Q"))
        ask_question_action.setShortcutVisibleInContextMenu(True)
        menu.addAction(ask_question_action)
        menu.addSeparator()


        #
        # submenus
        #
        submenu = QMenu("Modes", self)

        test_data_action = QAction("Test data", self)
        submenu.addAction(test_data_action)
        test_data_action.triggered.connect(self.on_test_data)

        test_delimiter_action = QAction("Test delimiter", self)
        submenu.addAction(test_delimiter_action)
        test_delimiter_action.triggered.connect(self.on_test_delimiter)

        test_quotechar_action = QAction("Test quotechar", self)
        submenu.addAction(test_quotechar_action)
        test_quotechar_action.triggered.connect(self.on_test_quotechar)

        submenu.addSeparator()

        error_action = QAction("Error", self)
        submenu.addAction(error_action)
        error_action.triggered.connect(self.on_error)

        explain_action = QAction("Explain", self)
        submenu.addAction(explain_action)
        explain_action.triggered.connect(self.on_explain)

        files_action = QAction("Files", self)
        submenu.addAction(files_action)
        files_action.triggered.connect(self.on_files)

        logic_action = QAction("Logic", self)
        submenu.addAction(logic_action)
        logic_action.triggered.connect(self.on_logic)

        print_action = QAction("Print", self)
        submenu.addAction(print_action)
        print_action.triggered.connect(self.on_print)

        return_action = QAction("Return", self)
        submenu.addAction(return_action)
        return_action.triggered.connect(self.on_return)

        run_action = QAction("Run", self)
        submenu.addAction(run_action)
        run_action.triggered.connect(self.on_run_mode)

        source_action = QAction("Source", self)
        submenu.addAction(source_action)
        source_action.triggered.connect(self.on_source)

        transfer_action = QAction("Transfer", self)
        submenu.addAction(transfer_action)
        transfer_action.triggered.connect(self.on_transfer)

        unmatched_action = QAction("Unmatched", self)
        submenu.addAction(unmatched_action)
        unmatched_action.triggered.connect(self.on_unmatched)

        validation_action = QAction("Validation", self)
        submenu.addAction(validation_action)
        validation_action.triggered.connect(self.on_validation)

        menu.addMenu(submenu)

        cursor = self.textCursor()
        position = cursor.position()

        if not sput.in_comment(self.toPlainText(), position):
            submenu.setEnabled(False)
        #
        # Show the menu
        #
        menu.exec(event.globalPos())
        #
        # Clean up
        #
        del menu

    def _insert_mode(self, m:str) -> None:
        if not self.desaved():
            return
        position = self.textCursor().position()
        self.setPlainText(sput.insert(text=self.toPlainText(), position=position, insert=m))
        self.desaved()

    def on_test_data(self) -> None:
        self._insert_mode("test-data: relative/path/to/file")

    def on_test_delimiter(self) -> None:
        self._insert_mode("test-delimiter:")

    def on_test_quotechar(self) -> None:
        self._insert_mode("test-quotechar:")

    def on_error(self) -> None:
        self._insert_mode("error-mode: full")

    def on_explain(self) -> None:
        self._insert_mode("explain-mode:")

    def on_files(self) -> None:
        self._insert_mode("files-mode:")

    def on_logic(self) -> None:
       self._insert_mode("logic-mode: AND")

    def on_print(self) -> None:
       self._insert_mode("print-mode:")

    def on_return(self) -> None:
       self._insert_mode("return-mode: matches")

    def on_run_mode(self) -> None:
       self._insert_mode("run-mode:")

    def on_source(self) -> None:
       self._insert_mode("source-mode:")

    def on_transfer(self) -> None:
       self._insert_mode("transfer-mode:")

    def on_unmatched(self) -> None:
       self._insert_mode("unmatched-mode: no-keep")

    def on_validation(self) -> None:
       self._insert_mode("validation-mode: print, no-raise")

    def on_generate_data(self) -> None:
        gen = GenerateCsvDialog(main=self.parent.main, path=self.parent.path)
        self.main.show_now_or_later(gen)

    def on_ask_question(self) -> None:
        gen = AskQuestionDialog(parent=self, main=self.parent.main, path=self.parent.path)
        self.main.show_now_or_later(gen)

    def on_load(self) -> None:
        loader = CsvpathLoader(self.parent.main)
        loader.load_paths(self.parent.path)

    def on_save_as(self, switch_local=False) -> None:
        #
        # in principle we could allow save-as for immutable files, but
        # atm keeping it simple. to save as you first have to copy back
        # to the working directory.
        #
        if self.editable == EditStates.UNEDITABLE:
            return
        #
        # if we are in an inputs or archive we're going to want to
        # send the copy to the left-hand side file tree.
        #
        # for that switch local must be True to let us know not to
        # use self.parent.path
        #
        # since we catch rt-clicks direct, we have to recheck
        # if switch_local should be true.
        #
        if not switch_local:
            apath = self.parent.path
            ap = self.main.csvpath_config.archive_path
            ncp = self.main.csvpath_config.inputs_csvpaths_path
            if apath.startswith(ap) or apath.startswith(ncp):
                switch_local=True
        thepath = None
        if switch_local:
            index = self.main.sidebar.last_file_index
            if index is not None:
                file_info = self.main.sidebar.file_model.fileInfo(index)
                thepath = file_info.filePath()
                if thepath is not None:
                    thepath = str(thepath)
            if thepath is None:
                thepath = self.main.state.cwd
            else:
                nos = Nos(thepath)
                if nos.isfile():
                    thepath = os.path.dirname(thepath)
        else:
            thepath = self.parent.path
            thepath = os.path.dirname(thepath)

        name = os.path.basename(self.parent.path)
        name, ok = meut.input(title="Save As", msg="Where should the new file live? ")
        if ok and name:
            text = self.toPlainText()
            path = fiut.deconflicted_path( thepath, name )
            with DataFileWriter( path=path ) as file:
                file.write(text)
            #
            # does this need to change if switch_local?
            #
            self.parent.open_file(path=path, data=None)
            self.parent.reset_saved()

    def _copy_back_question(self, action="edit") -> None:
        yes = meut.yesNo( parent=self, msg=f"You can't {action} here. Copy back to project?", title="Copy file to project?")
        if yes is True:
            try:
                name = self.parent.objectName()
                to_path = fiut.copy_results_back_to_cwd(main=self.main, from_path=name)
                self.main.read_validate_and_display_file_for_path(to_path)
                self.main.content.tab_widget.close_tab(name)
            except Exception:
                import traceback
                print(traceback.format_exc())


    def on_save(self) -> None:
        #
        # if the path is under the inputs or archive we have to save-as, not just save
        #
        # if the parent isn't editable we shouldn't get here, but if we did we need to
        # be sure to not save.
        #
        if self.editable == EditStates.UNEDITABLE:
            self._copy_back_question()
            return
        path = self.parent.path
        ap = self.main.csvpath_config.archive_path
        ncp = self.main.csvpath_config.inputs_csvpaths_path
        if path.startswith(ap) or path.startswith(ncp):
            self.on_save_as(switch_local=True)
            return

        with DataFileWriter(path=self.parent.path) as writer:
            writer.write(self.toPlainText())
        #
        # set the status bar
        #
        self.main.statusBar().showMessage(f"  Saved to: {self.parent.path}")
        self.parent.reset_saved()

    def on_run(self) -> None:
        if self.editable == EditStates.UNEDITABLE:
            self._copy_back_question("run")
            return
        cursor = self.textCursor()
        position = cursor.position()
        text = self.toPlainText()
        text = self.find_csvpath_at_position( position, text )
        self.parent.run_one_csvpath(text, position=position)

    def on_append(self) -> None:
        if self.editable == EditStates.UNEDITABLE:
            self._copy_back_question()
            return
        text = self.toPlainText()
        text = f"{text}\n\n---- CSVPATH ----\n\n~\n   id: \n~\n\n$[*][ yes() ]\n"
        self.setPlainText(text)
        self.desaved()

    def find_csvpath_at_position(self, position:int, text:str) -> str:
        #
        # split the text at the cursor into top and bottom
        # start = rfind marker in top or text[0]
        # end = rfind marker in bottom or text[len(text)-1]
        # glue the two halfs back together
        #
        if position < 0:
            #
            # would this ever happen? error dialog?
            #
            return
        if position > len(text)-1:
            #
            # would this ever happen? error dialog?
            #
            return
        top = text[0:position+1]
        bottom = text[position:]
        #
        # find markers if any
        #
        start = top.rfind(PathsManager.MARKER)+len(PathsManager.MARKER) if top.rfind(PathsManager.MARKER) > -1 else 0
        end = bottom.find(PathsManager.MARKER) if bottom.find(PathsManager.MARKER) > -1 else len(bottom)

        top2 = top[start:len(top)-1]
        bottom2 = bottom[0:end]

        text2 = f"{top2}{bottom2}"
        return text2

    def add_to_external_comment_of_csvpath_at_position(self, *, position:int, addto:str) -> str:
        text = self.toPlainText()
        text, d = self._add_to_external_comment_of_csvpath_at_position(text=text, position=position, addto=addto)
        self.setPlainText(text)

    @classmethod
    def _add_to_external_comment_of_csvpath_at_position(self, *, text:str, position:int, addto:str) -> tuple[str, dict]:
        #
        # text: the whole file
        # position: where the cursor is, indicating which csvpath
        # addto: information we want to add to the external comment
        #
        # we return the new string and a dict of the parts of the original string + the
        # additional metadata. the latter is only for debugging. it could go away, but
        # it does no harm to leave it while the code is new and the unit tests small.
        #
        if position >= len(text):
            raise ValueError(f"Index {position} out of string: {text}")
        #
        #                                                 V
        #$[*][ yes()] ---- CSVPATH ---- ~ two fish ~ $[*][ yes()] ---- CSVPATH ---- ~ three bugs ~ $[*][ yes() ]
        #|--------------------top-------------------------|----------bottom------------------------------------|
        #|--------------over-----------|------head--------|-tail--|---------under------------------------------|
        #                              |s|--comment-|-pre-|
        #                                /\
        #                               /m\
        #
        #
        top = None
        bottom = None
        over = None
        head = None
        tail = None
        under = None
        s = None
        comment = None
        pre = None
        #
        # find major parts
        #
        top = text[0:position]
        bottom = text[position:]
        _ = top.rfind(PathsManager.MARKER)
        if _ == -1:
            over = ""
            head = top
        else:
            over = top[0:_]
            head = top[_:]
        _ = bottom.find(PathsManager.MARKER)
        if _ == -1:
            tail = bottom
            under = ""
        else:
            tail = bottom[0:_]
            under = bottom[_:]
        #
        # parse head further
        #
        if head.find("~") > -1:
            _ = head.find("~")
            s = head[0:_+1]
            comment = head[_+1:head.rfind("~")+1]
            pre = head[head.rfind("~")+1:]
        else:
            s = "~"
            comment = "~"
            pre = head
        #
        # build the new string and collect the dict for checking, if needed.
        #
        return (
          f"{over}{s}{addto}{comment}{pre}{tail}{under}",
          {"over":over, "s":s, "addto":addto, "comment":comment,"pre":pre, "tail":tail, "under":under}
        )



