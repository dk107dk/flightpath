import os

from PySide6.QtWidgets import QLineEdit, QFormLayout, QPushButton

from csvpath.util.nos import Nos
from .blank_form import BlankForm

from flightpath.util.os_utility import OsUtility as osut
from flightpath.util.message_utility import MessageUtility as meut


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
        path = os.path.join(self.main.state.home, self.main.state.projects_home)
        nos = Nos(path)
        if not nos.exists():
            nos.makedirs()
            meut.message2(
                parent=self,
                msg=f"{path} does not exist. Creating it.",
                title="Not Found",
            )
        elif nos.isfile():
            #
            # TODO: this could, rarely, happen. we should alert the user of the misconfig.
            #
            meut.warning2(
                parent=self,
                msg=f"{path} is a file.",
                title="Cannot Open",
            )
        else:
            o = osut.file_system_open_cmd()
            os.system(f'{o} "{path}"')

    def _setup(self) -> None:
        self.project_dir.textChanged.connect(self.main.reactor.on_config_changed)

    def add_to_config(self, config) -> None:
        home = self.project_dir.text()
        path = os.path.join(self.main.state.home, home)
        if path:
            nos = Nos(path)
            if not nos.exists():
                try:
                    nos.makedirs()
                except Exception:
                    self.alert()
            if self.main.is_writable(path):
                self.main.state.projects_home = home
            else:
                self.project_dir.setText(self.original_projects_home)

    def alert(self) -> None:
        meut.warning2(
            parent=self,
            title="Not Writable",
            msg="Not a writable location. Your projects path has not been changed. Please pick another projects directory.",
        )

    def populate(self):
        self.original_projects_home = self.main.state.projects_home
        self.project_dir.setText(self.main.state.projects_home)

    @property
    def fields(self) -> list[str]:
        return []

    @property
    def server_fields(self) -> list[str]:
        return []

    @property
    def section(self) -> str:
        return ""

    @property
    def tabs(self) -> list[str]:
        return []
