import os
import traceback

from PySide6.QtWidgets import QWidget

from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter

from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.message_utility import MessageUtility as meut


#
# long overdue start on making the right side windows more DRY
#
class SidebarRightBase(QWidget):
    def update_style(self) -> None:
        try:
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
                meut.warning(
                    parent=self, title="Error", msg=f"Cannot copy file to {to_nos.path}"
                )
                return
            try:
                with DataFileReader(from_path) as ffrom:
                    with DataFileWriter(path=to_nos.path) as tto:
                        tto.write(ffrom.read())
            except NotADirectoryError:
                meut.warning(
                    parent=self, title="Error", msg="Cannot copy item over another file"
                )
        else:
            meut.warning(parent=self, title="Error", msg="Cannot copy item")
