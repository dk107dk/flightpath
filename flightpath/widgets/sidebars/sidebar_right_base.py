import os
import traceback

from PySide6.QtWidgets import QWidget, QMessageBox, QApplication

from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter


from flightpath.dialogs.find_file_by_reference_dialog import FindFileByReferenceDialog

from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.message_utility import MessageUtility as meut


class SidebarRightBase(QWidget):
    def refresh(self) -> None:
        if self.view:
            layout = self.layout()
            if layout:
                layout.removeWidget(self.view)
            self.view.deleteLater()
            self.setup()

    def _delete_item(self) -> None:
        index = self.view.currentIndex()
        if index.isValid():
            path = self.model.filePath(index)
            meut.yesNo2(
                parent=self,
                title="Delete",
                msg=f"Permanently delete {path}?",
                callback=self._do_delete_item,
                args={"path": path},
            )

    def _do_delete_item(self, answer: int, *, path: str) -> None:
        if answer == QMessageBox.Yes:
            nos = Nos(path)
            try:
                nos.remove()
            except OSError as e:
                meut.warning2(parent=self, title="Error", msg=str(e))
            else:
                self.window().statusBar().showMessage(f"{path} deleted")
                self.main.renew_sidebar_named_paths()
                self.main.welcome.update_run_button()
                self.main.welcome.update_find_data_button()

    def _delete_file_view_item(self) -> None:
        confirm = self._delete_item()
        if confirm is True:
            self.main.renew_sidebar_named_files()

    def _delete_paths_view_item(self) -> None:
        confirm = self._delete_item()
        if confirm is True:
            self.main.renew_sidebar_named_paths()

    def _delete_archive_view_item(self) -> None:
        confirm = self._delete_item()
        if confirm is True:
            self.main.renew_sidebar_archive()

    def _copy_path(self) -> None:
        from_index = self.view.currentIndex()
        if from_index.isValid():
            path = self.model.filePath(from_index)
            clipboard = QApplication.instance().clipboard()
            clipboard.setText(path)

    def _find_data(self):
        find = FindFileByReferenceDialog(main=self.main)
        self.main.show_now_or_later(find)

    def update_style(self) -> None:
        try:
            if self.model:
                self.model.set_style(self.view.style())
        except Exception:
            print(traceback.format_exc())

    def check_sftp(self, path: str) -> bool:
        if path is None:
            raise ValueError("Path cannot be None")
        nos = Nos(path)
        if not nos.is_sftp:
            return True
        s = "a" if str(self.config.get(section="sftp", name="server")).strip() else None
        s = str(self.config.get(section="sftp", name="port")).strip() if s else None
        s = str(self.config.get(section="sftp", name="username")).strip() if s else None
        s = str(self.config.get(section="sftp", name="password")).strip() if s else None
        return s is not None

    def _copy_back_to_cwd(self) -> None:
        from_index = self.view.currentIndex()
        if from_index.isValid():
            from_path = self.model.filePath(from_index)
            to_index = self.main.sidebar.file_navigator.currentIndex()
            to_path = None
            if to_index.isValid():
                to_path = self.main.sidebar.proxy_model.filePath(to_index)
            else:
                to_path = self.main.state.cwd
            to_nos = Nos(to_path)
            if to_nos.isfile():
                to_path = os.path.dirname(to_nos.path)
            to_dir = to_path
            from_name = os.path.basename(from_path)
            to_nos.path = os.path.join(to_dir, from_name)
            if to_nos.exists():
                to_path = fiut.deconflicted_path(to_dir, from_name)
                to_nos.path = to_path
            if to_nos.exists():
                meut.warning2(
                    parent=self, title="Error", msg=f"Cannot copy file to {to_nos.path}"
                )
                return
            try:
                with DataFileReader(from_path) as ffrom:
                    with DataFileWriter(path=to_nos.path) as tto:
                        tto.write(ffrom.read())
            except NotADirectoryError:
                meut.warning2(
                    parent=self, title="Error", msg="Cannot copy item over another file"
                )
        else:
            meut.warning2(parent=self, title="Error", msg="Cannot copy item")
