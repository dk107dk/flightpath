import os
from PySide6.QtWidgets import QPlainTextEdit, QInputDialog, QStyle
from PySide6.QtGui import QAction, QKeyEvent, QKeySequence, QShortcut, QPixmap, QPainter, QIcon
from PySide6.QtCore import Qt
from PySide6.QtSvg import QSvgRenderer

from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos
from csvpath.managers.paths.paths_manager import PathsManager

from flightpath.util.file_utility import FileUtility as fiut

class CsvPathTextEdit(QPlainTextEdit):

    def __init__(self, *, main, parent) -> None:
        super().__init__()
        self.main = main
        self.parent = parent
        self.icon = None
        self.parent.saved = True
        save_shortcut_ctrl_save = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut_cmd_save = QShortcut(QKeySequence("Command+S"), self)
        save_shortcut_ctrl_save.activated.connect(self.on_save)
        save_shortcut_cmd_save.activated.connect(self.on_save)
        save_shortcut_ctrl_run = QShortcut(QKeySequence("Ctrl+R"), self)
        save_shortcut_cmd_run = QShortcut(QKeySequence("Command+R"), self)
        save_shortcut_ctrl_run.activated.connect(self.on_run)
        save_shortcut_cmd_run.activated.connect(self.on_run)

    def keyPressEvent(self, event: QKeyEvent):
        if self.parent.saved is True:
            path = self.parent.path
            path = os.path.dirname(path)
            i = self.main.content.tab_widget.currentIndex()
            name = self.main.content.tab_widget.tabText(i)
            name = name.replace("+", "")
            self.main.content.tab_widget.setTabText(i, f"+ {name}" )
            self.main.statusBar().showMessage(f"{path}{os.sep}{name}+")
            self.parent.saved = False
        super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        #
        # separator and save options
        #
        menu.addSeparator()
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.on_save)
        menu.addAction(save_action)

        save_as_action = QAction("Save As", self)
        save_as_action.triggered.connect(self.on_save_as)
        menu.addAction(save_as_action)
        #
        # separator and run
        #
        menu.addSeparator()
        run_action = QAction("Run", self)
        run_action.triggered.connect(self.on_run)
        menu.addAction(run_action)
        #
        # Show the menu
        #
        menu.exec(event.globalPos())
        #
        # Clean up
        #
        del menu

    def on_save_as(self, switch_local=False) -> None:
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
                file_info = self.main.sidebar.file_model.fileInfo(source_index)
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
        #
        # if the path is under the inputs or archive we have to save-as, not just save
        #
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
        cursor = self.textCursor()
        position = cursor.position()
        text = self.toPlainText()
        text = self.find_csvpath_at_position( position, text )
        self.parent.run_one_csvpath(text)

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


