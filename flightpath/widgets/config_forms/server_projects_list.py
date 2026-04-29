from PySide6.QtWidgets import QListWidget, QMenu
from PySide6.QtCore import Qt, QPoint, Slot
from flightpath.util.message_utility import MessageUtility as meut


class ServerProjectsList(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.my_parent = parent

    def show_context_menu(self, pos: QPoint):
        global_pos = self.mapToGlobal(pos)

        menu = QMenu(self)
        refresh = menu.addAction("Refresh")
        menu.addSeparator()
        download_config = menu.addAction("Download config")
        download_env = menu.addAction("Download env")
        download_log = menu.addAction("Download log")
        menu.addSeparator()
        overwrite_config = menu.addAction("Upload config")
        sync_config = menu.addAction("Sync config")
        overwrite_env = menu.addAction("Sync env")
        menu.addSeparator()
        new_proj = menu.addAction("New project")
        menu.addSeparator()
        delete_proj = menu.addAction("Delete project")

        # Connect actions to slots (functions)
        refresh.triggered.connect(lambda: self.handle_action("refresh"))
        download_config.triggered.connect(lambda: self.handle_action("download_config"))
        download_env.triggered.connect(lambda: self.handle_action("download_env"))
        download_log.triggered.connect(lambda: self.handle_action("download_log"))
        overwrite_config.triggered.connect(lambda: self.handle_action("upload_config"))
        sync_config.triggered.connect(lambda: self.handle_action("sync_config"))
        overwrite_env.triggered.connect(lambda: self.handle_action("upload_env"))
        delete_proj.triggered.connect(self.delete_project)
        new_proj.triggered.connect(self.new_project)

        # Execute the menu at the global position
        menu.exec(global_pos)

    def handle_action(self, action: str) -> None:
        if action is None:
            raise ValueError("Action cannot be None")
        if action == "download_log":
            self.download_log()
        elif action == "download_config":
            self.download_config()
        elif action == "download_env":
            self.download_env()
        elif action == "upload_config":
            self.upload_config()
        elif action == "sync_config":
            self.sync_config()
        elif action == "upload_env":
            self.upload_env()
        elif action == "refresh":
            self.refresh()

    def refresh(self) -> None:
        self.my_parent.populate()

    def select_item_by_name(self, name):
        found_items = self.findItems(name, Qt.MatchExactly)
        if found_items:
            item_to_select = found_items[0]
            self.setCurrentItem(item_to_select)

    def upload_config(self) -> None:
        proj = self.currentItem()
        if proj:
            name = proj.text()
            self.my_parent._upload_config(name)
        else:
            meut.message2(
                parent=self, msg="Please select a project", title="Select project"
            )

    def sync_config(self) -> None:
        proj = self.currentItem()
        if proj:
            name = proj.text()
            self.my_parent._sync_config(name)
        else:
            meut.message2(
                parent=self, msg="Please select a project", title="Select project"
            )

    def upload_env(self) -> None:
        proj = self.currentItem()
        if proj:
            name = proj.text()
            self.my_parent._upload_env(name)
        else:
            meut.message2(
                parent=self, msg="Please select a project", title="Select project"
            )

    def download_log(self) -> None:
        proj = self.currentItem()
        if proj:
            name = proj.text()
            self.my_parent._download_log(name)
        else:
            meut.message2(
                parent=self, msg="Please select a project", title="Select project"
            )

    def download_config(self) -> None:
        proj = self.currentItem()
        if proj:
            name = proj.text()
            self.my_parent._download_config(name)
        else:
            meut.message2(
                parent=self, msg="Please select a project", title="Select project"
            )

    def download_env(self) -> None:
        proj = self.currentItem()
        if proj:
            name = proj.text()
            self.my_parent._download_env(name)
        else:
            meut.message2(
                parent=self, msg="Please select a project", title="Select project"
            )

    def delete_project(self) -> None:
        proj = self.currentItem()
        if proj:
            name = proj.text()
            self.my_parent._delete_project(name)
        else:
            meut.message2(
                parent=self, msg="Please select a project", title="Select project"
            )

    def new_project(self) -> None:
        meut.input2(
            parent=self,
            title="New server project",
            msg="Enter the new FlightPath Server project name",
            callback=self._new_project_complete,
        )

    @Slot(tuple)
    def _new_project_complete(self, t: tuple[str, bool]) -> None:
        proj, ok = t
        if not ok:
            return
        if str(proj) in ["", "None"]:
            meut.warning2(
                parent=self, msg="You must provide a project name", title="Name Project"
            )
            return
        self.my_parent._create_project(proj)
