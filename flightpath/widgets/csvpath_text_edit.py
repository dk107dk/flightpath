import os
from PySide6.QtWidgets import QPlainTextEdit, QInputDialog
from PySide6.QtGui import QAction, QKeyEvent, QKeySequence, QShortcut
from csvpath.util.file_writers import DataFileWriter
from csvpath.managers.paths.paths_manager import PathsManager

class CsvPathTextEdit(QPlainTextEdit):

    def __init__(self, *, main, parent) -> None:
        super().__init__()
        self.main = main
        self.parent = parent
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
            self.main._create_status_bar()
            i = self.main.content.tab_widget.currentIndex()
            name = self.main.content.tab_widget.tabText(i)
            name = name.replace("+", "")
            self.main.content.tab_widget.setTabText(i, f"+{name}" )
            self.parent.saved = False
        super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()

        # separator and save options
        menu.addSeparator()
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.on_save)
        menu.addAction(save_action)

        save_as_action = QAction("Save As", self)
        save_as_action.triggered.connect(self.on_save_as)
        menu.addAction(save_as_action)

        # separator and run
        menu.addSeparator()
        run_action = QAction("Run", self)
        run_action.triggered.connect(self.on_run)
        menu.addAction(run_action)

        # Show the menu
        menu.exec(event.globalPos())

        # Clean up
        del menu

    def on_save_as(self) -> None:
        ...
        name = os.path.basename(self.parent.path)
        name, ok = QInputDialog.getText(self, "Save As", self.tr("Enter the name of the new file:"), text=name)
        if ok and name:
            text = self.toPlainText()
            path = os.path.join( os.path.dirname(self.parent.path), name )
            with DataFileWriter( path=path ) as file:
                file.write(text)
            self.parent.open_file(path=path, data=None)
            #
            # what could go wrong?
            #

            #
            # what (non)visual do we need to reload / rename?
            #

            """
            try:
                file.rename(new_name)
            except IsADirectoryError:
                QMessageBox.warning(
                    self, self.tr("Error"), self.tr("Source is a file but destination a directory.")
                )
            except NotADirectoryError:
                QMessageBox.warning(
                    self, self.tr("Error"), self.tr("Source is a directory but destination a file.")
                )
            except PermissionError:
                QMessageBox.warning(self, self.tr("Error"), self.tr("Operation not permitted."))
            except OSError:
                QMessageBox.warning(self, self.tr("Error"), self.tr("File with this name already exists."))
            else:
                self.window().statusBar().showMessage(self.tr("Item renamed successfuly."))
            """

    def on_save(self) -> None:
        with DataFileWriter(path=self.parent.path) as writer:
            writer.write(self.toPlainText())
        #
        # set the status bar
        #
        self.main.statusBar().showMessage(self.tr(f"  Saved to: {self.parent.path}"))
        self.main.content.csvpath_source_view.reset_saved()

    def on_run(self) -> None:
        cursor = self.textCursor()
        position = cursor.position()
        text = self.toPlainText()
        text = self.find_csvpath_at_position( position, text )
        self.parent.run_one_csvpath(text)

    def find_csvpath_at_position( self, position:int, text:str ) -> str:
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


