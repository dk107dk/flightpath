from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from csvpath.managers.metadata import Metadata
from csvpath.managers.errors.error import Error


class SidebarArchiveListener:
    def __init__(self, *, item):
        self.item = item

    def metadata_update(self, mdata: Metadata) -> None:
        self.mdata = mdata
        if isinstance(mdata, Error):
            self.update_item_error(mdata)
        else:
            self.update_item_started(mdata)

    def update_item_error(self, mdata) -> None:
        self.item.metadata["status"] = "error"
        self.item.metadata["error_message"] = mdata.message

        js = mdata.to_json()
        js["uuid"] = mdata.uuid_string
        js["cwd"] = mdata.cwd
        js["pid"] = mdata.pid
        js["archive"] = mdata.archive_path
        js["named_files"] = mdata.named_files_root
        js["named_paths_root"] = mdata.named_paths_root
        js["hostname"] = mdata.hostname
        js["ip_address"] = mdata.ip_address
        js["username"] = mdata.username

        self.item.metadata["error_json"] = js

        if str(self.item.subtitle.text()).strip() == "":
            msg = mdata.message[0 : min(45, len(mdata.message))]
            self.item.subtitle.setText(msg)
        self.item.status_dot.setColor(QColor("#fa5252"))  # red
        QApplication.beep()

    def update_item_started(self, mdata) -> None:
        self.item.metadata["run_dir"] = mdata.run_home
        self.item.subtitle.setText(mdata.run_home)
        self.item.status = "Running"
