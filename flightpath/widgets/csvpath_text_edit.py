import os
from PySide6.QtWidgets import QPlainTextEdit, QInputDialog, QStyle, QMenu
from PySide6.QtGui import QAction, QKeyEvent, QKeySequence, QShortcut, QPixmap, QPainter, QIcon, QFont
from PySide6.QtCore import Qt
from PySide6.QtSvg import QSvgRenderer

from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos
from csvpath.managers.paths.paths_manager import PathsManager

from flightpath.util.csvpath_loader import CsvpathLoader
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.span_utility import SpanUtility as sput
from flightpath.util.os_utility import OsUtility as osut

class CsvPathTextEdit(QPlainTextEdit):

    def __init__(self, *, main, parent, editable=True) -> None:
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
        # we use the seqs to make sure we're not setting a doc to
        # desaved when we should just be reacting to a shortcut
        #
        self.short_seqs = []
        self.short_seqs.append(save_shortcut_ctrl.key())
        self.short_seqs.append(save_shortcut_ctrl.key())
        self.short_seqs.append(load_shortcut_ctrl.key())
        self.short_seqs.append(append_shortcut_ctrl.key())

        self.load_dialog = None

    def keyPressEvent(self, event: QKeyEvent):
        if self.editable is False:
            return
        super().keyPressEvent(event)
        t = event.text()
        if t and t != "":
            self.desaved()

    def desaved(self) -> bool:
        if self.editable is False:
            return False
        if self.parent.saved is True:
            path = self.parent.path
            path = os.path.dirname(path)
            i = self.main.content.tab_widget.currentIndex()
            name = self.main.content.tab_widget.tabText(i)
            name = name.replace("+", "")
            self.main.content.tab_widget.setTabText(i, f"+ {name}" )
            self.main.statusBar().showMessage(f"{path}{os.sep}{name}+")
            self.parent.saved = False
        return True

    def contextMenuEvent(self, event):
        if self.editable is not True:
            return
        menu = self.createStandardContextMenu()
        #
        # separator and save options
        #
        menu.addSeparator()
        save = "Save"
        save_action = QAction(save, self)
        save_action.triggered.connect(self.on_save)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.setShortcutVisibleInContextMenu(True)
        menu.addAction(save_action)

        save_as_action = QAction("Save as", self)
        save_as_action.triggered.connect(self.on_save_as)
        menu.addAction(save_as_action)
        #
        # separator and run
        #
        menu.addSeparator()
        load_action = QAction("Load to group", self)
        load_action.triggered.connect(self.on_load)
        load_action.setShortcut(QKeySequence("Ctrl+L"))
        load_action.setShortcutVisibleInContextMenu(True)
        menu.addAction(load_action)
        #
        # separator and run
        #
        #menu.addSeparator()
        run_action = QAction("Run", self)
        run_action.triggered.connect(self.on_run)
        run_action.setShortcut(QKeySequence("Ctrl+R"))
        run_action.setShortcutVisibleInContextMenu(True)
        menu.addAction(run_action)
        menu.addSeparator()
        append_action = QAction("Append a csvpath", self)
        append_action.triggered.connect(self.on_append)
        append_action.setShortcut(QKeySequence("Shift+Ctrl+A"))
        append_action.setShortcutVisibleInContextMenu(True)
        menu.addAction(append_action)
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

        match_action = QAction("Match", self)
        submenu.addAction(match_action)
        match_action.triggered.connect(self.on_match)

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
        self._insert_mode("test-data:")

    def on_test_delimiter(self) -> None:
        self._insert_mode("test-delimiter:")

    def on_test_quotechar(self) -> None:
        self._insert_mode("test-quotechar:")

    def on_error(self) -> None:
        self._insert_mode("error-mode:")

    def on_explain(self) -> None:
        self._insert_mode("explain-mode:")

    def on_files(self) -> None:
        self._insert_mode("files-mode:")

    def on_logic(self) -> None:
       self._insert_mode("logic-mode:")

    def on_match(self) -> None:
       self._insert_mode("match-mode:")

    def on_print(self) -> None:
       self._insert_mode("print-mode:")

    def on_return(self) -> None:
       self._insert_mode("return-mode:")

    def on_run_mode(self) -> None:
       self._insert_mode("run-mode:")

    def on_source(self) -> None:
       self._insert_mode("source-mode:")

    def on_transfer(self) -> None:
       self._insert_mode("transfer-mode:")

    def on_unmatched(self) -> None:
       self._insert_mode("unmatched-mode:")

    def on_validation(self) -> None:
       self._insert_mode("validation-mode:")

    def on_load(self) -> None:
        loader = CsvpathLoader(self.parent.main)
        loader.load_paths(self.parent.path)

    def on_save_as(self, switch_local=False) -> None:
        #
        # in principle we could allow save-as for immutable files, but
        # atm keeping it simple. to save as you first have to copy back
        # to the working directory.
        #
        if self.editable is False:
            return
        #
        # if we are in an inputs or archive we're going to want to
        # send the copy to the left-hand side file tree.
        #
        # for that switch local must be True to let us know not to
        # use self.parent.path
        #
        # sadly, since we catch rt-clicks direct, we have to recheck
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
        name, ok = QInputDialog.getText(self, "Save As", "Where should the new file go? ", text=name)
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

    def on_save(self) -> None:
        print(f"csvpath_text_edit: on_save!")
        #
        # if the path is under the inputs or archive we have to save-as, not just save
        #
        # if the parent isn't editable we shouldn't get here, but if we did we need to
        # be sure to not save.
        #
        if self.editable is False:
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
        if self.editable is False:
            return
        cursor = self.textCursor()
        position = cursor.position()
        text = self.toPlainText()
        text = self.find_csvpath_at_position( position, text )
        self.parent.run_one_csvpath(text)

    def on_append(self) -> None:
        if self.editable is False:
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


