import os
from PySide6.QtWidgets import QTextEdit, QMenu
from PySide6.QtGui import QAction, QKeyEvent, QKeySequence, QShortcut
from PySide6.QtCore import Qt, QFileInfo

from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos

from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.os_utility import OsUtility as osut

class MdTextEdit(QTextEdit):

    def __init__(self, *, main, parent, editable=True) -> None:
        super().__init__()
        self.main = main
        self.parent = parent
        self.editable = editable
        self.parent.saved = True
        #
        #
        #
        save_shortcut_ctrl = QShortcut(QKeySequence("Ctrl+s"), self)
        save_shortcut_ctrl.activated.connect(self.parent.on_save)

        toggle_shortcut_ctrl = QShortcut(QKeySequence("Ctrl+t"), self)
        toggle_shortcut_ctrl.activated.connect(self.parent.on_toggle)
        #
        # we use the seqs to make sure we're not setting a doc to
        # desaved when we should just be reacting to a shortcut
        #
        self.short_seqs = []
        self.short_seqs.append(save_shortcut_ctrl.key())
        self.short_seqs.append(toggle_shortcut_ctrl.key())

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
            name = name.replace("+ ", "")
            self.main.content.tab_widget.setTabText(i, f"+ {name}" )
            self.main.statusBar().showMessage(f"{path}{os.sep}{name}+")
            self.parent.saved = False
        return True

    def contextMenuEvent(self, event):
        if self.editable is not True:
            return
        menu = self.createStandardContextMenu()

        #
        # separator and toggle raw edit
        #
        path = self.parent.path
        if path.endswith(".md"):
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
        menu.addAction(save_as_action)
        #
        # Show the menu
        #
        menu.exec(event.globalPos())
        #
        # Clean up
        #
        del menu


