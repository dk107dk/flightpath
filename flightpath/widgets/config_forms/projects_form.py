import os

from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QWidget,
)

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
        layout.addRow("Name of projects directory: ", self.project_dir)

        note = QLabel(
            "Stored in ~/.flightpath — not in this project's config.ini. "
            "Applies to all projects. "
            "The Config panel Save and Reset buttons do not affect this setting."
        )
        note.setWordWrap(True)
        layout.addRow("", note)

        open_button = QPushButton("Open projects dir")
        open_button.clicked.connect(self.on_click_open)

        self.set_button = QPushButton("Set Directory")
        self.set_button.setEnabled(False)
        self.set_button.clicked.connect(self.on_set_directory)

        buttons = QWidget()
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons.setLayout(buttons_layout)
        buttons_layout.addWidget(open_button)
        buttons_layout.addWidget(self.set_button)
        layout.addRow("", buttons)

        self.setLayout(layout)
        self._setup()

    def _setup(self) -> None:
        self.project_dir.textChanged.connect(self._on_dir_changed)

    def _on_dir_changed(self, text: str) -> None:
        current = self.main.state.projects_home if self.main and self.main.state else ""
        self.set_button.setEnabled(text.strip() != "" and text.strip() != current)

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
            meut.warning2(
                parent=self,
                msg=f"{path} is a file.",
                title="Cannot Open",
            )
        else:
            o = osut.file_system_open_cmd()
            os.system(f'{o} "{path}"')

    def on_set_directory(self) -> None:
        if self.main._has_config_changes():
            meut.message2(
                parent=self,
                title="Unsaved Config Changes",
                msg="Save or reset config changes before switching the projects directory.",
            )
            return
        new_home = self.project_dir.text().strip()
        if not new_home:
            return
        meut.yesNo2(
            parent=self,
            title="Change Projects Directory",
            msg=(
                f"Change the projects directory to '{new_home}'? "
                "This affects all projects in FlightPath and switches to the Default project."
            ),
            callback=self._on_confirm_set_directory,
            args={"new_home": new_home},
        )

    def _on_confirm_set_directory(self, answer: int, *, new_home: str) -> None:
        if answer != QMessageBox.Yes:
            self.project_dir.setText(self.main.state.projects_home)
            self.set_button.setEnabled(False)
            return
        path = os.path.join(self.main.state.home, new_home)
        nos = Nos(path)
        if not nos.exists():
            try:
                nos.makedirs()
            except Exception:
                self.alert()
                self.project_dir.setText(self.main.state.projects_home)
                self.set_button.setEnabled(False)
                return
        if not self.main.is_writable(path):
            self.alert()
            self.project_dir.setText(self.main.state.projects_home)
            self.set_button.setEnabled(False)
            return
        self.main.state.projects_home = new_home
        self.main.state.current_project = self.main.state.DEFAULT_PROJECT_NAME
        self.main.load_state_and_cd()
        self.main.cancel_config_changes()

    def alert(self) -> None:
        meut.warning2(
            parent=self,
            title="Not Writable",
            msg="Not a writable location. Your projects path has not been changed. Please pick another projects directory.",
        )

    def add_to_config(self, config) -> None:
        pass

    def populate(self):
        self.original_projects_home = self.main.state.projects_home
        self.project_dir.setText(self.main.state.projects_home)
        self.set_button.setEnabled(False)

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
