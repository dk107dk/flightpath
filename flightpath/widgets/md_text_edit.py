import os
from PySide6.QtWidgets import QTextEdit
from PySide6.QtGui import QAction, QKeyEvent, QKeySequence


from flightpath.util.key_utility import KeyUtility as keut

from flightpath.util.editable import EditStates


class MdTextEdit(QTextEdit):
    def __init__(self, *, main, parent, editable=EditStates.EDITABLE) -> None:
        super().__init__()
        self.main = main
        self.my_parent = parent
        self.editable = editable
        self.my_parent.saved = True

    def keyPressEvent(self, event: QKeyEvent):
        if self.editable == EditStates.UNEDITABLE:
            return
        super().keyPressEvent(event)
        if keut.is_edit_key(event):
            self.desaved()

    def desaved(self) -> bool:
        if self.editable == EditStates.UNEDITABLE:
            return False
        if self.my_parent.saved is True:
            path = self.my_parent.path
            path = os.path.dirname(path)
            i = self.main.content.tab_widget.currentIndex()
            name = self.main.content.tab_widget.tabText(i)
            name = name.replace("+ ", "")
            self.main.content.tab_widget.setTabText(i, f"+ {name}")
            self.main.statusBar().showMessage(f"{path}{os.sep}{name}+")
            self.my_parent.saved = False
        return True

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
        path = self.my_parent.path
        if path.endswith(".md"):
            menu.addSeparator()
            t = "Toggle view"
            t_action = QAction(t, self)
            t_action.triggered.connect(self.my_parent.on_toggle)
            t_action.setShortcut(QKeySequence("Ctrl+T"))
            t_action.setShortcutVisibleInContextMenu(True)
            menu.addAction(t_action)
        #
        # separator and save options
        #
        menu.addSeparator()
        save = "Save"

        save_action = QAction(save, self)
        save_action.triggered.connect(self.my_parent.on_save)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.setShortcutVisibleInContextMenu(True)
        menu.addAction(save_action)

        save_as_action = QAction("Save as", self)
        save_as_action.triggered.connect(self.my_parent.on_save_as)
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
