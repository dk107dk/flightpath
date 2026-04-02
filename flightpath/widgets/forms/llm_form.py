import os
from PySide6.QtWidgets import QLineEdit, QFormLayout, QCheckBox, QPushButton

from flightpath.util.generator_utility import GeneratorUtility as geut
from flightpath.util.os_utility import OsUtility as osut
from flightpath.util.file_utility import FileUtility as fiut

from csvpath.util.nos import Nos
from .blank_form import BlankForm


class LlmForm(BlankForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QFormLayout()
        self.model = QLineEdit()
        layout.addRow("AI Model: ", self.model)

        self.base = QLineEdit()
        layout.addRow("API base: ", self.base)

        self.key = QLineEdit()
        layout.addRow("API key: ", self.key)

        self.checkbox = QCheckBox("")
        self.checkbox.setChecked(True)
        layout.addRow("Use for all projects: ", self.checkbox)

        button = QPushButton("Open metadata dir")
        layout.addRow("", button)
        button.clicked.connect(self.on_click_open)

        self.setLayout(layout)
        self._setup()

    def on_click_open(self) -> None:
        gconfig = geut.new_generator_config(main=self.main)
        path = gconfig.configpath
        path = os.path.dirname(path)
        cpath = gconfig.get(section="storage", name="root")
        path = fiut.join_local_overlapped(path, cpath)
        nos = Nos(path)
        if not nos.exists():
            nos.makedirs()
        elif nos.isfile():
            #
            # TODO: this could, rarely, happen. we should alert the user of the misconfig.
            #
            print(f"LlmForm: on_click_open: {path} is a file. Cannot open.")
        else:
            o = osut.file_system_open_cmd()
            os.system(f'{o} "{path}"')

    def _setup(self) -> None:
        self.model.textChanged.connect(self.main.on_config_changed)
        self.base.textChanged.connect(self.main.on_config_changed)
        self.key.textChanged.connect(self.main.on_config_changed)
        self.checkbox.stateChanged.connect(self.main.on_config_changed)

    def add_to_config(self, config) -> None:
        config.add_to_config("llm", "model", self.model.text().strip())
        config.add_to_config("llm", "api_base", self.base.text().strip())
        config.add_to_config("llm", "api_key", self.key.text().strip())
        if self.checkbox.isChecked():
            data = self.main.state.data
            ai = data.get("llm")
            if ai is None:
                ai = {}
                data["llm"] = ai
            ai["model"] = self.model.text().strip()
            ai["api_base"] = self.base.text().strip()
            ai["api_key"] = self.key.text().strip()
            self.main.state.data = data

    def _llm_config_matches_state(self) -> bool:
        data = self.main.state.data
        ai = data.get("llm", {})

        _ = self.config.get(section="llm", name="model", default="")
        if _ == "":
            return False
        if ai.get("model") != _:
            return False

        _ = self.config.get(section="llm", name="api_base", default="")
        if _ == "":
            return False
        if ai.get("api_base") != _:
            return False

        _ = self.config.get(section="llm", name="api_key", default="")
        if _ == "":
            return False
        if ai.get("api_key") != _:
            return False

        return True

    def populate(self):
        #
        # we'll populate from .flightpath but not save. if the user doesn't hit save
        # config.ini will still have blanks, but we'll check .flightpath when AI is
        # actually used, so there won't be a gap.
        #
        data = self.main.state.data
        ai = data.get("llm", {})
        config = self.config

        local = False
        _ = config.get(section="llm", name="model", default="")
        local = local if _ == "" else True
        _ = ai.get("model", "") if _ == "" else _
        self.model.setText(_)

        _ = config.get(section="llm", name="api_base", default="")
        _ = ai.get("api_base", "") if _ == "" and local is False else _
        self.base.setText(_)

        _ = config.get(section="llm", name="api_key", default="")
        _ = ai.get("api_key", "") if _ == "" and local is False else _
        self.key.setText(_)

        self.checkbox.setChecked(self._llm_config_matches_state())

    @property
    def fields(self) -> list[str]:
        return ["model", "api_base", "api_key"]

    @property
    def server_fields(self) -> list[str]:
        return self.fields

    @property
    def section(self) -> str:
        return "llm"

    @property
    def tabs(self) -> list[str]:
        return []
