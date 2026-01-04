import os
import json
from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QLabel,
    QComboBox
)

from csvpath.util.config import Config
from csvpath.util.nos import Nos
from .blank_form import BlankForm

class ConfigForm(BlankForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QFormLayout()
        self.config_dir_path = QLineEdit()
        layout.addRow("Config file path: ", self.config_dir_path)
        msg = QLabel("The default is config/config.ini")
        msg.setStyleSheet("QLabel { font-size: 12pt; font-style:italic;color:#222222;}")
        layout.addRow("", msg)
        self.allow_var_sub = QComboBox()
        layout.addRow("Allow variable substitution: ", self.allow_var_sub)
        self.var_sub_source = QLineEdit()
        layout.addRow("Variable substitution source: ", self.var_sub_source)

        msg = QLabel(
"""The default is env, meaning use OS env vars; otherwise,
 a path to a JSON dict.""")
        msg.setStyleSheet("QLabel { font-size: 12pt; font-style:italic;color:#222222;}")
        layout.addRow("", msg)

        self.setLayout(layout)
        self._setup()

    def _setup(self) -> None:
        self.config_dir_path.textChanged.connect(self.main.on_config_changed)
        self.allow_var_sub.activated.connect(self.main.on_config_changed)
        self.var_sub_source.textChanged.connect(self.main.on_config_changed)

    def add_to_config(self, config) -> None:
        path = self.config_dir_path.text()
        if path is None or path.strip() == "":
            path = f"config{os.sep}config.ini"
        elif not path.endswith(f"{os.sep}config.ini"):
            path = f"{path}{os.sep}config.ini"
        self.config.add_to_config("config", "path", path )
        self.config.add_to_config("config", "allow_var_sub", self.allow_var_sub.currentText() )
        path = self.var_sub_source.text()
        path = "env" if path is None or path.strip() == "" else path
        if path != "env":
            path = ConfigForm.make_path(path=path, cwd=self.main.state.cwd, current_project=self.main.state.current_project)
            path = self.assure_env_path(path)
        self.config.add_to_config("config", "var_sub_source", path )
        path = self.var_sub_source.setText(path)

    @classmethod
    def make_path(self, *, path:str, cwd:str, current_project:str) -> str:
        if not path or path.strip() in ["", "env"]:
            return "env"
        if cwd is None:
            raise ValueError("Current project path cannot be None")
        if current_project is None:
            current_project = os.path.basename(cwd)
        path = path.strip().lower()
        cwd = cwd.strip().lower()
        current_project = current_project.strip().lower()
        proj = f"{current_project}{os.sep}"
        i = path.find(proj)
        if i >= 0:
            path = path[i+len(proj):]
            if path.startswith(f"config{os.sep}"):
                path = f"{cwd}{os.sep}{path}"
            else:
                path = f"{cwd}{os.sep}config{os.sep}{path}"
        elif path.startswith(os.sep):
            path = os.path.basename(path)
            path = f"{cwd}{os.sep}config{os.sep}{path}"
        elif path.startswith(f"config{os.sep}"):
            path = f"{cwd}{os.sep}{path}"
        else:
            path = f"{cwd}{os.sep}config{os.sep}{path}"
        return path

    def assure_env_path(self, path:str) -> str:
        if path is None:
            path = f"config{os.sep}env.json"
        if path.endswith(f"{os.sep}config.ini"):
            path = f"config{os.sep}env.json"
        if not path.endswith(".json"):
            path = f"{path}.json"
            self.var_sub_source.setText(path)
        if not os.path.exists(path):
            d = os.path.dirname(path)
            if not os.path.exists(d):
                Nos(d).makedirs()
            with open(path, "w") as file:
                json.dump({}, file, indent=2)
        return path

    def populate(self):
        config = self.config
        config_path = config.get(section="config", name="path", default="config/config.ini")
        self.config_dir_path.setText(config_path)

        self.allow_var_sub.clear()
        self.allow_var_sub.addItem("yes")
        self.allow_var_sub.addItem("no")
        allow = config.get(section="config", name="allow_var_sub", default="yes")
        allow = allow.strip().lower()
        #
        # no is correct, but we'll take false because it's a reasonable guess.
        # everything else indicates yes.
        #
        if allow in ["no", "false"]:
            self.allow_var_sub.setCurrentText("no")
        else:
            self.allow_var_sub.setCurrentText("yes")

        env_path = config.get(section="config", name="var_sub_source", default="env")
        self.var_sub_source.setText(env_path)

    @property
    def fields(self) -> list[str]:
        return ["path", "allow_var_sub", "var_sub_source"]

    @property
    def server_fields(self) -> list[str]:
        return []

    @property
    def section(self) -> str:
        return "config"

    @property
    def tabs(self) -> list[str]:
        return []

