from PySide6.QtWidgets import QListWidget, QMenu
from PySide6.QtCore import Qt, QPoint
from flightpath.util.message_utility import MessageUtility as meut

class ServerProjectsList(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.parent = parent

    def show_context_menu(self, pos: QPoint):
        global_pos = self.mapToGlobal(pos)

        menu = QMenu(self)
        download_config = menu.addAction("Download config")
        download_env = menu.addAction("Download env")
        download_log = menu.addAction("Download log")
        menu.addSeparator()
        overwrite_config = menu.addAction("Upload config")
        overwrite_env = menu.addAction("Upload env")
        menu.addSeparator()
        new_proj = menu.addAction("New project")
        menu.addSeparator()
        delete_proj = menu.addAction("Delete project")

        # Connect actions to slots (functions)
        download_config.triggered.connect(lambda: self.handle_action("download_config"))
        download_env.triggered.connect(lambda: self.handle_action("download_env"))
        download_log.triggered.connect(lambda: self.handle_action("download_log"))
        overwrite_config.triggered.connect(lambda: self.handle_action("upload_config"))
        overwrite_env.triggered.connect(lambda: self.handle_action("upload_env"))
        delete_proj.triggered.connect(self.delete_project)
        new_proj.triggered.connect(self.new_project)

        # Execute the menu at the global position
        menu.exec(global_pos)

    def handle_action(self, action:str) -> None:
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
        elif action == "upload_env":
            self.upload_env()





    def upload_config(self) -> None:
        proj = self.currentItem()
        if proj:
            name = proj.text()
            print(f"set config for project named: {name}")
            self.parent._upload_config(name)
        else:
            meut.message(msg="Please select a project", title="Select project")




    def upload_env(self) -> None:
        proj = self.currentItem()
        if proj:
            name = proj.text()
            print(f"set env for project named: {name}")
            self.parent._upload_env(name)
        else:
            meut.message(msg="Please select a project", title="Select project")








    def download_log(self) -> None:
        proj = self.currentItem()
        if proj:
            name = proj.text()
            print(f"get log for project named: {name}")
            self.parent._download_log(name)
        else:
            meut.message(msg="Please select a project", title="Select project")

    def download_config(self) -> None:
        proj = self.currentItem()
        if proj:
            name = proj.text()
            print(f"get config for project named: {name}")
            self.parent._download_config(name)
        else:
            meut.message(msg="Please select a project", title="Select project")

    def download_env(self) -> None:
        proj = self.currentItem()
        if proj:
            name = proj.text()
            print(f"get env for project named: {name}")
            self.parent._download_env(name)
        else:
            meut.message(msg="Please select a project", title="Select project")

    def delete_project(self) -> None:
        proj = self.currentItem()
        if proj:
            name = proj.text()
            print(f"delete project named: {name}")
            self.parent._delete_project(name)
        else:
            meut.message(msg="Please select a project", title="Select project")

    def new_project(self) -> None:
        proj, ok = meut.input(title="New server project", msg="Enter the new FlightPath Server project name")
        if ok and proj and proj.strip() != "":
            self.parent._create_project(proj)

