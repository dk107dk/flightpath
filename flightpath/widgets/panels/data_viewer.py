import os
import csv
import io
import json
import traceback
from typing import Any

from PySide6.QtCore import Qt, Slot, QPoint, QSize, QMimeData, QThread, QCoreApplication
from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QStackedLayout,
        QTableView,
        QLabel,
        QMenu,
        QApplication,
        QInputDialog
)
from PySide6.QtGui import QPixmap, QPainter, QShortcut, QKeySequence, QAction, QStandardItem, QKeyEvent
from PySide6.QtSvg import QSvgRenderer

from csvpath.util.line_spooler import CsvLineSpooler

from flightpath.widgets.panels.table_model import TableModel
from flightpath.util.style_utils import StyleUtility as stut
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.message_utility import MessageUtility as meut
from flightpath.editable import EditStates

from .raw_viewer import RawViewer

class DataViewer(QWidget):

    def __init__(self, parent, *, editable:EditStates=EditStates.UNEDITABLE):
        super().__init__()
        #
        # sets the font size
        #
        stut.set_common_style(self)
        #
        #
        #
        self.parent = parent
        self.main = parent.main
        self.path = self.main.selected_file_path
        self.main_layout = QStackedLayout()
        self.setLayout(self.main_layout)
        self.table_view = QTableView()
        #
        # not sure what this was
        #
        #self.content_view = self.table_view
        #
        # attempt to debug the last row ctx menu prob
        #
        #self.table_view.verticalHeader().setStretchLastSection(False)

        self.editable = editable
        self.table_view.editable = self.editable
        stut.set_editable_background(self.table_view)

        self.table_view.hide()
        self.raw_view = RawViewer(main=self.main, parent=self, editable=self.editable)
        stut.set_editable_background(self.raw_view)

        self.main_layout.addWidget(self.table_view)
        self.main_layout.addWidget(self.raw_view)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        #
        # the list of int representing the lines we display. the
        # raw viewer needs the same lines
        #
        self.lines_to_take = None
        self.saved = True
        #
        # keyboard shortcuts
        #
        if self.is_editable:
            load_shortcut_save = QShortcut(QKeySequence("Ctrl+s"), self)
            load_shortcut_save.activated.connect(self.on_save)
            load_shortcut_save = QShortcut(QKeySequence("Ctrl+a"), self)
            load_shortcut_save.activated.connect(self.on_save_as)
        #
        # context menu
        #
        if self.is_editable:
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self._show_context_menu)

    @property
    def is_editable(self) -> bool:
        return self.editable == EditStates.EDITABLE


    def _show_context_menu(self, position: QPoint):
        # `position` is in the QTableView's coordinates.
        # map it to the viewport's coordinates for calculations
        viewport_position = self.table_view.viewport().mapFrom(self.table_view, position)

        # use viewport_position for all calculations
        index = self.table_view.indexAt(viewport_position)
        row = self.table_view.rowAt(viewport_position.y())

        if row < 0:
            last_row_index = self.table_view.model().rowCount() - 1
            if last_row_index >= 0:
                last_cell_rect = self.table_view.visualRect(self.table_view.model().index(last_row_index, 0))
                if viewport_position.y() > last_cell_rect.bottom():
                    row = last_row_index

        # The mapToGlobal call must be made from the widget that emitted the signal.
        global_position = self.table_view.mapToGlobal(position)

        if row == -1:
            row = self.table_view.rowAt(position.y())
        if index.isValid() or row > -1:
            row = index.row()
            context_menu = QMenu(self)

            save_action = QAction()
            save_action.setText("Save")
            save_action.triggered.connect(self.on_save)
            context_menu.addAction(save_action)

            save_as_action = QAction()
            save_as_action.setText("Save As")
            save_as_action.triggered.connect(self.on_save_as)
            context_menu.addAction(save_as_action)

            context_menu.addSeparator()

            if row > -1:
                insert_line_above_action = QAction()
                insert_line_above_action.setText("Insert line above")
                insert_line_above_action.triggered.connect(lambda: self._insert_line_above(row))
                context_menu.addAction(insert_line_above_action)

            insert_line_below_action = QAction()
            t = "Insert line below" if row > -1 else "Insert line at 0"
            insert_line_below_action.setText(t)
            insert_line_below_action.triggered.connect(lambda: self._insert_line_below(row))
            context_menu.addAction(insert_line_below_action)

            context_menu.addSeparator()

            delete_line_action = QAction()
            delete_line_action.setText("Delete line")
            delete_line_action.triggered.connect(lambda: self._delete_line(row))
            context_menu.addAction(delete_line_action)

            context_menu.addSeparator()

            if index.column() > -1:
                insert_header_left_action = QAction()
                insert_header_left_action.setText("Insert header left")
                insert_header_left_action.triggered.connect(lambda: self._insert_header_left(index.column()))
                context_menu.addAction(insert_header_left_action)

            insert_header_right_action = QAction()
            t = "Insert header right" if index.column() > -1 else "Insert header at 0"
            insert_header_right_action.setText(t)
            insert_header_right_action.triggered.connect(lambda: self._insert_header_right(index.column()))
            context_menu.addAction(insert_header_right_action)

            context_menu.addSeparator()

            delete_header_action = QAction()
            delete_header_action.setText("Delete header")
            delete_header_action.triggered.connect(lambda: self._delete_header(index.column()))
            context_menu.addAction(delete_header_action)
            #
            #
            #
            selection_model = self.table_view.selectionModel()
            indexes = selection_model.selectedIndexes()
            if len(indexes) > 0:
                context_menu.addSeparator()
                to_new_action = QAction()
                to_new_action.setText("Copy to new file")
                to_new_action.triggered.connect(self._copy_to_new)
                context_menu.addAction(to_new_action)
            context_menu.exec(global_position)
        else:
            print(f"index not valid: {index}: {index.row()}, {index.column()}; row: {row}")

    def _relative_path_to_parent_dir(self) -> str:
        path = os.path.dirname(self.path)
        i = path.rfind(self.main.state.current_project)
        path = path[i+len(self.main.state.current_project):]
        path = path.lstrip(os.sep)
        return path

    def _copy_to_new(self) -> None:
        dialog = QInputDialog()
        dialog.setFixedSize(QSize(420, 125))
        dialog.setLabelText("Enter the new CSV file's name (ending with .csv):")
        dialog.setTextValue(self._relative_path_to_parent_dir())
        ok = dialog.exec()
        new_name = dialog.textValue()
        if ok and new_name:
            new_name = os.path.join(self.main.state.cwd, new_name)
            b, msg = self._valid_new_file(new_name)
            if b is True:
                ns = fiut.split_filename(new_name)
                try:
                    if not new_name.startswith(self.main.state.cwd):
                        new_name = os.path.join(self.main.state.cwd, new_name)
                    self._write_new_from_selected(new_name)
                except PermissionError:
                    QMessageBox.warning(self, "Error", "Operation not permitted.")
                except OSError:
                    QMessageBox.warning(self, "Error", "File with this name already exists.")
            else:
                self.window().statusBar().showMessage(self.tr("Bad file name"))
                meut.warning(parent=self, msg=msg, title="Cannot create file")
                return

    def _from_coord(self, row:int, column:int) -> Any:
        selection_model = self.table_view.selectionModel()
        indexes = selection_model.selectedIndexes()
        for i, _ in enumerate(indexes):
            if _.row() == row and _.column() == column:
                return self.table_view.model().data(_, Qt.ItemDataRole.DisplayRole)
        return ""

    def _write_new_from_selected(self, path:str) -> None:
        selection_model = self.table_view.selectionModel()
        indexes = selection_model.selectedIndexes()
        #
        # create a grid
        #
        clow = min( [_.column() for _ in indexes] )
        chigh = max( [_.column() for _ in indexes] )
        rlow = min( [_.row() for _ in indexes] )
        rhigh = max( [_.row() for _ in indexes] )

        lst = []
        for row in range(rlow,rhigh+1):
            line = []
            lst.append(line)
            for column in range(clow,chigh+1):
                line.append(self._from_coord(row, column))

        lines = CsvLineSpooler(None, path=path)
        for _ in lst:
            lines.append(_)
        lines.close()

    def _valid_new_file(self, name:str) -> tuple[bool,str]:
        if name is None or name.strip() == "":
            return False, "Name cannot be empty"
        if (
            (name.find("/") > -1 or name.find("\\") > -1)
            and not ( name.startswith(self.main.state.cwd) or name.startswith(f".{os.sep}") )
        ):
            return False, "File must be in or below the working directory"
        if not name.endswith(".csv", 1):
            return False, "Filename must end in .csv"
        return True, "Ok"

    @Slot(int)
    def _delete_line(self, at:int) -> None:
        selection_model = self.table_view.selectionModel()
        selected_indexes = selection_model.selectedIndexes()
        cells = [at]
        for _ in selected_indexes:
            if _.row() not in cells:
                cells.append(_.row())
        cells.sort(reverse=True)
        for _ in cells:
            self.table_view.model().remove_rows(_, 1)

    @Slot(int)
    def _delete_header(self, at:int) -> None:
        selection_model = self.table_view.selectionModel()
        selected_indexes = selection_model.selectedIndexes()
        cells = [at]
        for _ in selected_indexes:
            if _.column() not in cells:
                cells.append(_.column())
        cells.sort(reverse=True)
        for _ in cells:
            self.table_view.model().remove_columns(_, 1)

    @Slot(int)
    def _insert_line_below(self, at:int) -> None:
        self._new_line(at + 1, 1)

    @Slot(int)
    def _insert_line_above(self, at:int) -> None:
        self._new_line(at, 1)

    def _new_line(self, at:int, number:int) -> None:
        if at < 0 or at > self.table_view.model().rowCount():
            print(f"Cannot insert a line at {at}")
            return
        model = self.table_view.model()
        i = model.columnCount()
        line = ["" for _ in range(i) ]
        model.insertRows( at, 1, line )
        self.mark_unsaved()

    @Slot(int)
    def _insert_header_right(self, at:int) -> None:
        self._new_header(at+1, 1)

    @Slot(int)
    def _insert_header_left(self, at:int) -> None:
        self._new_header(at, 1)

    def _append_header(self) -> None:
        at = self.table_view.model().columnCount()
        self._new_header(at, 1)

    def _new_header(self, at:int, number:int) -> None:
        model = self.table_view.model()
        model.insertColumns( at, 1 )
        self.mark_unsaved()


    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        key_text = event.text()
        if self.is_editable and (key == Qt.Key.Key_Delete or key == Qt.Key_Backspace):
            self.delete_selected_cells()
        #
        # can always tab
        #
        elif self.is_editable and key == Qt.Key.Key_Tab:
            ...
        #
        # can always copy
        #
        elif event.matches(QKeySequence.StandardKey.Copy):
            self.copy_selection_to_clipboard()
        #
        # only paste if editable
        #
        elif (
              self.is_editable
              and event.key() == Qt.Key.Key_V
              and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            self.paste_from_clipboard()

        elif self.is_editable and key == Qt.Key_Right:
            selection_model = self.table_view.selectionModel()
            selected_indexes = selection_model.selectedIndexes()
            if selected_indexes and len(selected_indexes) == 1:
                index = selected_indexes[0]
                col = index.column()
                if col + 1 == self.table_view.model().columnCount():
                    self._insert_header_right(col)

        elif self.is_editable and key == Qt.Key_Down:
            selection_model = self.table_view.selectionModel()
            selected_indexes = selection_model.selectedIndexes()
            if selected_indexes and len(selected_indexes) == 1:
                index = selected_indexes[0]
                row = index.row()
                if row + 1 == self.table_view.model().rowCount():
                    self._insert_line_below(row)
        else:
            ...

        #
        # if we're editable we'll keep the event. remember that editability of
        # individual cells is controled by the TableModel's editable value.
        #
        if self.is_editable:
            #
            # hand up for further
            #
            super().keyPressEvent(event)
        else:
            event.ignore()


    def delete_selected_cells(self):
        model = self.table_view.model()
        selection_model = self.table_view.selectionModel()
        selected_indexes = selection_model.selectedIndexes()
        if not selected_indexes:
            return
        # Sort the indexes to ensure changes are applied consistently
        # (e.g., if you were deleting rows/columns, sorting by row/column desc is crucial)
        # For simply clearing cell data, sorting is less critical but good practice.
        selected_indexes.sort(key=lambda index: (index.row(), index.column()))
        for index in selected_indexes:
            if index.isValid() and (model.flags(index) & Qt.ItemFlag.ItemIsEditable):
                model.setData(index, "", Qt.ItemDataRole.EditRole)
            else:
                print(f"Cell at ({index.row()}, {index.column()}) is not editable or invalid.")

    def copy_selection_to_clipboard(self):
        selection_model = self.table_view.selectionModel()
        selected_indexes = selection_model.selectedIndexes()
        if not selected_indexes:
            return
        pairs = []
        for index in selected_indexes:
            row = index.row()
            col = index.column()
            data = self.table_view.model().data(self.table_view.model().index(row, col), Qt.ItemDataRole.DisplayRole)
            pairs.append( ( row, col, data if data is not None else "" ) )
        jsons = json.dumps(pairs, indent=2)
        print("\nDataViewer: starting clipboard operation")
        clipboard = QApplication.clipboard()
        print("DataViewer: clearing clipboard")
        #
        # on windows this will often report failure but actually succeed due to a retry in the Qt code.
        # adding our own retry loop has been suggested, but atm the processEvents() call seems to clear
        # out any locks and adding a retry without processEvents() didn't help. since adding
        # processEvents() we haven't had problems.
        #
        clipboard.clear()
        print("DataViewer: processing events")
        QApplication.processEvents()
        print("DataViewer: Clipboard mode:", clipboard.supportsSelection())
        print("DataViewer: Clipboard text before:", clipboard.text())
        print("DataViewer: supportsSelection:", clipboard.supportsSelection())
        print("DataViewer: ownsClipboard:", clipboard.ownsClipboard())
        print("DataViewer: ownsFindBuffer:", clipboard.ownsFindBuffer())
        print(f"DataViewer: on main thread: {(QThread.currentThread() == QCoreApplication.instance().thread())}")
        mime = QMimeData()
        mime.setText(jsons)
        print("DataViewer: setting mime data to clipboard")
        clipboard.setMimeData(mime)
        print("DataViewer: set mime data to clipboard. done.\n")

    def paste_from_clipboard(self):
        clipboard = QApplication.clipboard()
        pasted_text = clipboard.text()
        if not pasted_text:
            meut.message(msg="There is nothing to paste", title="Clipboard Error")
            return

        pcells = json.loads(pasted_text)
        start_index = self.table_view.selectionModel().currentIndex()
        if not start_index.isValid():
            meut.message(msg="Select a cell to paste into", title="Clipboard Error")
            return

        source_x = pcells[0][0]
        source_y = pcells[0][1]

        dest_x = start_index.row()
        dest_y = start_index.column()

        for i, _ in enumerate(pcells):
            if i == 0:
                #
                # copy 1st data to new selected. no translation.
                #
                target_index = self.table_view.model().index(dest_x, dest_y)
                if target_index.isValid():
                    self.table_view.model().setData(target_index, _[2], Qt.ItemDataRole.EditRole)
            else:
                add_x = _[0] - source_x
                add_y = _[1] - source_y
                madd_x = add_x
                madd_y = add_y
                the_x = dest_x+add_x
                the_y = dest_y+add_y
                target_index = self.table_view.model().index( the_x, the_y)
                if target_index.isValid():
                    self.table_view.model().setData(target_index, _[2], Qt.ItemDataRole.EditRole)

    def toggle_grid_raw(self):
        i = self.layout().currentIndex()
        i = 0 if i == 1 else 1
        #
        if i == 1:
        #
            self.show_raw()
        #
        else:
        #
            self.show_grid()
        #
        self.layout().setCurrentIndex(i)

    def show_grid(self) -> None:
        if self.saved is False:
            w = self.layout().widget(1)
            data = []
            try:
                file = io.StringIO(w.text_edit.toPlainText())
                delimiter = self.main.content.toolbar.delimiter_char()
                quotechar= self.main.content.toolbar.quotechar_char()
                reader = csv.reader(
                    file, delimiter=delimiter, quotechar=quotechar
                )
                for line in reader:
                    data.append(line)
            finally:
                file.close()
            #
            # add data to table model, clearing table model first
            #
            table_model = TableModel(data=data, editable=self.editable)
            self.display_data(table_model)

    def show_raw(self) -> None:
        w = self.layout().widget(1)
        if w.loaded == False and self.saved is True:
            p = self.objectName()
            w.open_file(p, self.lines_to_take)
        #
        # if i == 1 (meaning we're going to show raw)
        # and raw is not loaded
        # and grid has changed: self.saved == False
        #
        if self.saved is False:
            cstr = self._write_to_string()
            self.raw_view.text_edit.setPlainText(cstr)
            self.raw_view.loaded = True

    """
    def toggle_grid_raw(self):
        i = self.layout().currentIndex()
        i = 0 if i == 1 else 1
        w = self.layout().widget(1)
        #
        # if i == 1 (meaning we're going to show raw)
        # and raw is not loaded
        # and grid is not changed: self.saved == True
        #
        if i == 1 and w.loaded == False and self.saved is True:
            p = self.objectName()
            w.open_file(p, self.lines_to_take)
        #
        # if i == 1 (meaning we're going to show raw)
        # and raw is not loaded
        # and grid has changed: self.saved == False
        #
        if i == 1 and self.saved is False:
            #
            # load the unsaved content from the grid view
            #
            cstr = self._write_to_string()
            self.raw_view.text_edit.setPlainText(cstr)
            self.raw_view.loaded = True
        self.layout().setCurrentIndex(i)
    """

    def on_save_as(self, switch_local=False, *, info=None) -> None:
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
            apath = self.path
            ap = self.main.csvpath_config.archive_path
            ncp = self.main.csvpath_config.inputs_csvpaths_path
            if apath.startswith(ap) or apath.startswith(ncp):
                switch_local=True
            thepath = self.path
            thepath = os.path.dirname(thepath)

        msg = "Where should the new file live? "
        if info is not None:
            msg = f"{info}\n\n{msg}"
        name = os.path.basename(self.path)
        name, ok = meut.input(
            title="Save As",
            msg=msg,
            text=thepath
        )
        if ok and name:
            path = fiut.deconflicted_path( thepath, name )
            self._save(path)

    @Slot()
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
        ap = self.main.csvpath_config.archive_path
        ncp = self.main.csvpath_config.inputs_csvpaths_path
        if (
            self.path.endswith(".jsonl") or
            self.path.endswith(".ndjson") or
            self.path.endswith(".json") or
            self.path.endswith(".jsonlines")
        ):
            msg = "Saving JSONL converts the data to CSV."
            #meut.message(msg=msg)
            self.on_save_as(info=msg)
            return
        if self.path.startswith(ap) or self.path.startswith(ncp):
            self.on_save_as(switch_local=True)
            return
        self._save(self.path)

    def _save(self, path:str) -> None:
        if path is None:
            raise ValueError("Path cannot be None")
        ns = fiut.split_filename(path)
        exts = self.main.csvpath_config.get(section="extensions", name="csv_files")
        if ns[1] not in exts:
            meut.warning(parent=self, title="Bad Filename", msg="The path must end in a data format extension")
            self.on_save_as()
            return
        self._save_csv(path)

        """
        if path.endswith(".csv"):
        else:
            self._save_jsonl(path)
        """

    def _save_jsonl(self, path:str) -> None:
        lines = JsonlLineSpooler(path=path)
        for _ in range(self.table_view.model().rowCount()):
            line = [
                self.table_view.model().data(self.table_view.model().index(_, col), Qt.ItemDataRole.DisplayRole)
                for col in range(self.table_view.model().columnCount())
            ]
            lines.append(line)
        lines.close()

    def _save_csv(self, path:str) -> None:
        #
        # get a line spooler. it uses a DataFileWriter to get a file-like
        # smart-open behind the scenes and then uses the native csv module
        # to do the writes. a bit convoluted, but that's the way CsvPath
        # does it, in order to allow for both lists in memory and files,
        # with files being in any of the backends.
        #
        lines = CsvLineSpooler(None, path=path) # we don't use a Result object
        for _ in range(self.table_view.model().rowCount()):
            line = [
                self.table_view.model().data(self.table_view.model().index(_, col), Qt.ItemDataRole.DisplayRole)
                for col in range(self.table_view.model().columnCount())
            ]
            lines.append(line)
        lines.close()
        #
        # set the status bar
        #
        self.main.statusBar().showMessage(f"  Saved to: {self.path}")
        self.reset_saved()

    def _write_to_string(self) -> str:
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer)
        for _ in range(self.table_view.model().rowCount()):
            line = [
                self.table_view.model().data(self.table_view.model().index(_, col), Qt.ItemDataRole.DisplayRole)
                for col in range(self.table_view.model().columnCount())
            ]
            writer.writerow(line)
        cstr = buffer.getvalue()
        buffer.close()
        return cstr

    def _copy_back_question(self, action="edit") -> None:
        yes = meut.yesNo( parent=self, msg=f"You can't {action} here. Copy back to project?", title="Copy file to project?")
        if yes is True:
            try:
                name = self.parent.objectName()
                to_path = fiut.copy_results_back_to_cwd(main=self.main, from_path=name)
                self.main.read_validate_and_display_file_for_path(to_path)
                self.main.content.tab_widget.close_tab(name)
            except Exception:
                print(traceback.format_exc())

    @Slot(tuple)
    def on_row_or_column_edit(self, fromf:tuple[int,int]) -> None:
        self.mark_unsaved()

    @Slot(tuple)
    def on_edit_made(self, xy:tuple[int,int, Any, Any]) -> None:
        if xy[2] != xy[3]:
            self.mark_unsaved()
            #
            # other actions?
            #

    def reset_saved(self) -> None:
        self.saved = True
        i = self.main.content.tab_widget.currentIndex()
        name = self.main.content.tab_widget.tabText(i)
        if name[0] == "+":
            name = name[1:]
            self.main.content.tab_widget.setTabText(i, name )
        #
        # exp!
        #
        # if we saved we can reload the raw view to get the most recent
        # bits from disk.
        #
        self.layout().widget(1).loaded = False

    def mark_unsaved(self) -> None:
        self.saved = False
        i = self.main.content.tab_widget.currentIndex()
        name = self.main.content.tab_widget.tabText(i)
        if name[0] != "+":
            name = f"+{name}"
            self.main.content.tab_widget.setTabText(i, name )

    def display_data(self, model):
        self.table_view.setModel(model)
        self.main.show_now_or_later(self.table_view)
        self.main.show_now_or_later(self.parent.toolbar)
        self.layout().setCurrentIndex(0)

    def clear(self, model):
        self.table_view.setModel(model)
        self.table_view.hide()
        self.parent.toolbar.hide()
        self.layout().setCurrentIndex(0)

