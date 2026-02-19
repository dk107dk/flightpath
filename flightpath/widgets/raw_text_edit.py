import os
from PySide6.QtWidgets import QPlainTextEdit, QMenu, QWidget
from PySide6.QtGui import QAction, QKeyEvent, QKeySequence, QShortcut
from PySide6.QtCore import Qt, QFileInfo

from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos

from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.os_utility import OsUtility as osut

from flightpath.editable import EditStates

class RawTextEdit(QPlainTextEdit):

    def __init__(self, *, main, parent, editable=EditStates.EDITABLE) -> None:
        super().__init__()
        self.main = main
        self.parent = parent

        print(f"rawtextedit: main: {main}, parent: {parent}")

        self.editable = editable
        self.parent.saved = True


    def keyPressEvent(self, event: QKeyEvent):
        if self.editable == EditStates.UNEDITABLE:
            return
        super().keyPressEvent(event)
        t = event.text()
        if t and t != "":
            self.desaved()

    def desaved(self) -> bool:
        return self.parent.desaved()
        """
        if self.editable == EditStates.UNEDITABLE:
            return False
        if self.parent.saved is True:
            path = self.parent.path
            path = os.path.dirname(path)
            i = self.main.content.tab_widget.currentIndex()
            name = self.main.content.tab_widget.tabText(i)
            name = name.replace("+ ", "")
            self.main.content.tab_widget.setTabText(i, f"+ {name}" )
            self.main.statusBar().showMessage(f"{path}{os.sep}{name}+")
            self.parent.saved = False
        return True
        """

    def contextMenuEvent(self, event):
        if self.editable == EditStates.UNEDITABLE:
            return
        menu = self.createStandardContextMenu()

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
        # separator and toggle raw edit
        #
        menu.addSeparator()
        t = "Toggle edit"
        t_action = QAction(t, self)
        t_action.triggered.connect(self.parent.on_toggle)
        t_action.setShortcut(QKeySequence("Ctrl+T"))
        t_action.setShortcutVisibleInContextMenu(True)
        menu.addAction(t_action)

        #
        # separator and save options
        #
        menu.addSeparator()
        save = "Save"
        save_action = QAction(save, self)
        save_action.triggered.connect(self.parent.on_save)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.setShortcutVisibleInContextMenu(True)
        menu.addAction(save_action)

        save_as_action = QAction("Save as", self)
        save_as_action.triggered.connect(self.parent.on_save_as)
        save_as_action.setShortcut(QKeySequence("Shift+Ctrl+S"))
        save_as_action.setShortcutVisibleInContextMenu(True)
        menu.addAction(save_as_action)

        #
        # Show the menu
        #
        menu.exec(event.globalPos())
        #
        # Clean up
        #
        del menu


