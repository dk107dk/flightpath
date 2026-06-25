import os

from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QMessageBox,
    QInputDialog,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import QSize

from csvpath.util.nos import Nos
from csvpath.util.path_util import PathUtility as pathu

from flightpath.dialogs.stage_data_dialog import StageDataDialog
from flightpath.actions.csvpath_loader import CsvpathLoader
from flightpath.util.editable import EditStates
from flightpath.util.os_utility import OsUtility as osut
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.message_utility import MessageUtility as meut
from flightpath.util.tabs_utility import TabsUtility as taut


class SidebarActions:
    def __init__(self, *, main: QMainWindow, parent: QWidget):
        super().__init__()
        self.main = main
        self.my_parent = parent

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _current_path(self) -> str | None:
        """Return the file path for the currently selected tree item, or None."""
        index = self.my_parent.file_navigator.currentIndex()
        if index.isValid():
            return self.my_parent.proxy_model.filePath(index)
        return None

    def _csvpath_extensions(self) -> set:
        return set(
            self.main.csvpath_config.get(section="extensions", name="csvpath_files")
        )

    def _csv_extensions(self) -> set:
        return set(self.main.csvpath_config.get(section="extensions", name="csv_files"))

    # -------------------------------------------------------------------------
    # Project
    # -------------------------------------------------------------------------

    def _on_project_changed(self) -> None:
        if self.my_parent.combo_building is True:
            return
        proj = self.my_parent.projects.currentText()
        if proj == self.main.state.current_project:
            return
        if proj == self.my_parent.NEW_PROJECT:
            self.my_parent.new_project_name(callback=self._make_new_project)
            return
        #
        # we need to clear the Config panel and reload it or let it lazy load
        #
        self.main.state.current_project = proj
        self.main.load_state_and_cd()
        self.main.cancel_config_changes()

    def _make_new_project(self, proj: str) -> None:
        """Called by the sidebar, not the context menu."""
        if proj is None:
            # Reset the combobox back to the current project
            index = self.my_parent.projects.findText(self.main.state.current_project)
            if index >= 0:
                self.my_parent.projects.setCurrentIndex(index)
        else:
            self.main.state.current_project = proj
            self.main.load_state_and_cd()
            self.main.cancel_config_changes()

    # -------------------------------------------------------------------------
    # AI actions
    # -------------------------------------------------------------------------

    def _on_explain(self, activity: str = None) -> None:
        path = self._current_path() or self.main.state.cwd
        # Open the file first — if this fails we don't want the AI tab open with nothing to show
        self.main.read_validate_and_display_file_for_path(path)
        self.main.rt_tabs_show()
        self.main.rt_tab_widget.tabBar().setCurrentIndex(1)
        self.main.reactor.on_ai_explain()

    def _generate_csvpath(self) -> None:
        path = self._current_path()
        if path is None:
            return
        self.main.read_validate_and_display_file_for_path(path)
        self.main.rt_tabs_show()
        self.main.rt_tab_widget.tabBar().setCurrentIndex(1)
        self.main.reactor.on_ai_gen_csvpath()

    def _generate_csv(self) -> None:
        path = self._current_path()
        if path is None:
            return
        self.main.read_validate_and_display_file_for_path(path)
        self.main.rt_tabs_show()
        self.main.rt_tab_widget.tabBar().setCurrentIndex(1)
        self.main.reactor.on_ai_gen_data()

    # -------------------------------------------------------------------------
    # Data operations
    # -------------------------------------------------------------------------

    def _stage_data(self) -> None:
        path = self._current_path()
        if path is None:
            return
        self.my_parent.stage_dialog = StageDataDialog(
            main=self.main, path=path, parent=self.my_parent
        )
        self.my_parent.stage_dialog.show_dialog()

    def _load_paths(self) -> None:
        path = self._current_path()
        if path is None:
            return
        loader = CsvpathLoader(main=self.main, parent=self)
        loader.load_paths(path)

    # -------------------------------------------------------------------------
    # Clipboard
    # -------------------------------------------------------------------------

    def _cut(self) -> None:
        path = self._current_path()
        if path is not None:
            self.my_parent.cutted = path

    def _copy(self) -> None:
        path = self._current_path()
        if path is not None:
            self.my_parent.copied = path

    def _paste(self) -> None:
        if self.my_parent.cutted is None and self.my_parent.copied is None:
            return
        path = self._current_path() or self.main.state.cwd
        if self.my_parent.cutted:
            name = os.path.basename(self.my_parent.cutted)
            dest = os.path.join(path, name)
            Nos(self.my_parent.cutted).rename(dest)
        elif self.my_parent.copied:
            name = os.path.basename(self.my_parent.copied)
            dest = fiut.deconflicted_path(path, name)
            Nos(self.my_parent.copied).copy(dest)
        self.my_parent.cutted = None
        self.my_parent.copied = None

    def _copy_path(self) -> None:
        path = self._current_path()
        if path is None:
            raise RuntimeError("An item must be selected to copy a relative path")
        path = pathu.resep(path)
        cwd = self.main.state.cwd
        if path.startswith(cwd):
            path = path[len(cwd) + 1 :]
        else:
            raise ValueError(f"Path must start with {cwd}. {path} does not.")
        QGuiApplication.clipboard().setText(path)

    def _copy_full_path(self) -> None:
        path = self._current_path() or self.main.state.cwd
        QGuiApplication.clipboard().setText(pathu.resep(path))

    # -------------------------------------------------------------------------
    # File system navigation
    # -------------------------------------------------------------------------

    def _open_file_navigator_location(self) -> None:
        path = self._current_path() or self.main.state.cwd
        path = pathu.resep(path)
        if Nos(path).isfile():
            path = os.path.dirname(path)
        cmd = f'{osut.file_system_open_cmd()} "{path}"'
        os.system(cmd)

    def _open_project_dir(self) -> None:
        path = pathu.resep(self.main.state.cwd)
        cmd = f'{osut.file_system_open_cmd()} "{path}"'
        os.system(cmd)

    # -------------------------------------------------------------------------
    # Rename / delete
    # -------------------------------------------------------------------------

    def _rename_file_navigator_item(self) -> None:
        path = self._current_path()
        if path is None:
            return
        dir_name = os.path.dirname(path)
        name = os.path.basename(path)

        dialog = QInputDialog()
        dialog.setFixedSize(QSize(420, 125))
        dialog.setLabelText("Enter new name:")
        dialog.setTextValue(name)
        ok = dialog.exec()
        new_name = dialog.textValue()

        if not (ok and new_name and new_name.strip() and new_name != name):
            return

        if os.sep in new_name:
            new_dir = os.path.dirname(new_name)
            np = os.path.normpath(os.path.join(dir_name, new_dir))
            if not np.startswith(self.main.state.cwd):
                meut.warning2(
                    parent=self.my_parent,
                    title="Path error",
                    msg=f"Error: invalid path: {np}",
                )
                return
            nos = Nos(np)
            if not nos.exists():
                try:
                    nos.makedirs()
                except Exception:
                    meut.warning2(
                        parent=self.my_parent,
                        title="Path error",
                        msg=f"Error: invalid path: {np}",
                    )
                    return

        Nos(path).rename(os.path.join(dir_name, new_name))

    def _delete_file_navigator_item(self) -> None:
        path = self._current_path()
        if path is None:
            return
        path = str(path)
        is_selected = self.my_parent.window().selected_file_path == path
        meut.yesNo2(
            parent=self.my_parent,
            title="Delete",
            msg=f"Are you sure you want to delete {path}?",
            callback=self._do_delete_item,
            args={"path": path, "is_selected": is_selected},
        )

    def _do_delete_item(self, answer: int, *, path: str, is_selected: bool) -> None:
        if path is None:
            raise ValueError("Path cannot be None")
        if answer == QMessageBox.Yes:
            try:
                Nos(path).remove()
            except OSError as e:
                meut.warning2(parent=self.my_parent, title="Error", msg=str(e))
            else:
                if is_selected:
                    self.my_parent.window().show_welcome_screen()
                self.my_parent.window().statusBar().showMessage(
                    f"{path} deleted successfully."
                )

    # -------------------------------------------------------------------------
    # New file / folder
    # -------------------------------------------------------------------------

    def _new_file_navigator_item(self) -> None:
        dialog = QInputDialog()
        dialog.setFixedSize(QSize(420, 125))
        dialog.setLabelText("Enter the new file's name:")
        ok = dialog.exec()
        new_name = dialog.textValue()
        if not (ok and new_name):
            return

        b, msg = self.my_parent._valid_new_file(new_name)
        if not b:
            self.my_parent.window().statusBar().showMessage(
                self.my_parent.tr("Bad file name")
            )
            button = QMessageBox.critical(
                self.my_parent,
                "Cannot create file",
                msg,
                buttons=QMessageBox.Cancel | QMessageBox.Retry,
                defaultButton=QMessageBox.Cancel,
            )
            if button == QMessageBox.Retry:
                self._new_file_navigator_item()
            return

        content = self._initial_content_for(new_name)
        if content is None:
            return  # user cancelled or unknown extension — error already shown

        dest = self._resolve_new_item_path(new_name)
        dest = fiut.deconflicted_path(os.path.dirname(dest), os.path.basename(dest))
        try:
            with open(dest, "w", encoding="utf-8") as f:
                f.write(content)
            self.main.statusBar().showMessage(f"  Created: {os.path.basename(dest)}")
        except PermissionError:
            meut.warning2(
                parent=self.my_parent, title="Error", msg="Operation not permitted."
            )
        except OSError as ex:
            meut.warning2(
                parent=self.my_parent,
                title="Error",
                msg=f"Could not create file: {ex}",
            )

    def _initial_content_for(self, new_name: str) -> str | None:
        """Return the starter content for a new file, or None to abort."""
        ext = fiut.split_filename(new_name)[1]

        if ext in ["json", "jsonl", "ndjson", "jsonlines"]:
            items = ["{}", "[]"]
            item, ok = QInputDialog.getItem(
                self.my_parent, "Data structure", "Start with", items, 0, False
            )
            return item if ok else None

        if ext == "md":
            return "# Title\n*(hit control-t to toggle to raw markdown editing)*\n"

        if ext == "txt":
            return ""

        if ext in self._csv_extensions():
            return ","

        if ext in self._csvpath_extensions():
            testdata = ""
            example = os.path.join(self.main.state.cwd, "examples/test.csv")
            if Nos(example).exists():
                testdata = "examples/test.csv"
            return (
                f"~\n   id: hello world\n   test-data: {testdata}\n~\n\n"
                '$[*][ print("hello world") ]'
            )

        meut.warning2(
            parent=self.my_parent, title="Error", msg="Unknown file extension"
        )
        return None

    def _save_file_navigator_item(self):
        self.main.content.csvpath_source_view.text_edit.on_save()

    def _new_folder_navigator_item(self) -> None:
        dialog = QInputDialog()
        dialog.setFixedSize(QSize(420, 125))
        dialog.setLabelText("Enter the new folder name: ")
        ok = dialog.exec()
        new_name = dialog.textValue()
        if not (ok and new_name):
            return

        b, msg = self.my_parent._valid_new_folder(new_name)
        if not b:
            self.my_parent.window().statusBar().showMessage(
                self.my_parent.tr("Bad folder name")
            )
            button = QMessageBox.critical(
                self.my_parent,
                "Cannot create folder",
                msg,
                buttons=QMessageBox.Cancel | QMessageBox.Retry,
                defaultButton=QMessageBox.Cancel,
            )
            if button == QMessageBox.Retry:
                self._new_folder_navigator_item()
            return

        dest = self._resolve_new_item_path(new_name)
        try:
            os.mkdir(dest)
        except PermissionError:
            meut.warning2(
                parent=self.my_parent, title="Error", msg="Operation not permitted."
            )
        except OSError:
            meut.warning2(
                parent=self.my_parent,
                title="Error",
                msg="File with this name already exists.",
            )

    def _resolve_new_item_path(self, name: str) -> str:
        """Resolve an absolute path for a new file or folder being created."""
        if name.startswith(self.main.state.cwd):
            return name
        if self.my_parent._last_path is None:
            return os.path.join(self.main.state.cwd, name)
        base = os.path.join(self.main.state.cwd, self.my_parent._last_path)
        return os.path.join(base, name)

    # -------------------------------------------------------------------------
    # reading
    # -------------------------------------------------------------------------

    def _load_worksheet(self, name: str) -> None:
        path = f"{self._current_path()}#{name}"
        self.main.read_validate_and_display_file_for_path(path)

    # -------------------------------------------------------------------------
    # JSON editing
    # -------------------------------------------------------------------------

    def _edit_as_json(self) -> None:
        path = self._current_path()
        if path is None:
            return
        self._do_edit_as_json(path)

    def _do_edit_as_json(self, path: str) -> None:
        if path is None:
            raise ValueError("Path cannot be None")
        if not Nos(path).isfile():
            return
        # Close any existing tab for this file before reopening as JSON
        data_view = taut.find_tab(self.main.content.tab_widget, path)
        if data_view is not None:
            self.main.content.tab_widget.close_tab(path)
        self.main.spin_up_json_worker(path=path, editable=EditStates.EDITABLE)
