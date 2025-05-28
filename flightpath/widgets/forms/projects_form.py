import os

from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QPushButton,
    QMessageBox,
    QLabel
)

from csvpath.util.config import Config
from csvpath.util.nos import Nos
from flightpath.util.os_utility import OsUtility as osut
from .blank_form import BlankForm

class ProjectsForm(BlankForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_projects_home = None

        layout = QFormLayout()
        self.project_dir = QLineEdit()
        self.project_dir.setReadOnly(True)
        layout.addRow("Name of projects directory: ", self.project_dir)
        button = QPushButton("Open projects dir")
        layout.addRow("", button)

        button.clicked.connect(self.on_click_open)

        self.setLayout(layout)
        self._setup()

    def on_click_open(self) -> None:
        path = os.path.join( self.main.state.home, self.main.state.projects_home)
        nos = Nos(path)
        if not nos.exists():
            print(f"ProjectsForm: on_click_open: {path} doesn't exist. Creating it.")
            nos.makedirs()
        elif nos.isfile():
            #
            # TODO: this could, rarely, happen. we should alert the user of the misconfig.
            #
            print(f"ProjectsForm: on_click_open: {path} is a file. Cannot open.")
        else:
            o = osut.file_system_open_cmd()
            print(f"ProjectsForm: on_click_open: opening {path} with {o}")
            os.system(f'{o} "{path}"')
        print(f"ProjectsForm: on_click_open: done.")

    def _setup(self) -> None:
        self.project_dir.textChanged.connect(self.main.on_config_changed)

    def add_to_config(self, config) -> None:
        home = self.project_dir.text()
        path = os.path.join(self.main.state.home, home)
        if path:
            nos = Nos(path)
            if not nos.exists():
                try:
                    nos.makedirs()
                except Exception as e:
                    print("ProjectsForm: add_to_config: error: {type(e)}: {e}")
                    self.alert()
            if self.main.is_writable(path):
                print(f"ProjectsForm: add_to_config: {path} is writable")
                self.main.state.projects_home = home
            else:
                print(f"ProjectsForm: add_to_config: {path} is not writable")
                self.project_dir.setText(self.original_projects_home)


    def alert(self) -> None:
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Not writable")
        msg_box.setText(f"{path} is not a writable location. Your projects path has not been changed. Please pick another projects directory.")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()


    def populate(self):
        self.original_projects_home = self.main.state.projects_home
        self.project_dir.setText(self.main.state.projects_home)


