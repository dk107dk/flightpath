import os
import re

from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QVBoxLayout,
    QPushButton,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QLabel
)

from csvpath.util.box import Box
from csvpath.util.nos import Nos
from csvpath.util.config_env import ConfigEnv
from flightpath.util.os_utility import OsUtility as osut
from .blank_form import BlankForm

class EnvForm(BlankForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(4, 0, 2, 0)
        self.setLayout(self.layout)
        box = QWidget()
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        box.setLayout(form_layout)
        self.layout.addWidget(box)

        self.filter_input = QLineEdit()
        form_layout.addRow("Filter: ", self.filter_input)
        self.env_value = QLineEdit()
        button = QPushButton("Update filter")
        form_layout.addRow("", button)
        button.clicked.connect(self._on_click_update)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Name", "Value"])
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        self.table.itemChanged.connect(self._on_item_changed)
        self.layout.addWidget(self.table)

        add = QWidget()
        add_form_layout = QFormLayout()
        add_form_layout.setContentsMargins(0, 0, 0, 0)
        add.setLayout(add_form_layout)
        self.layout.addWidget(add)

        add_form_inputs = QWidget()
        add_form_inputs_layout = QVBoxLayout()
        add_form_inputs_layout.setContentsMargins(0, 0, 0, 0)

        add_form_inputs.setLayout(add_form_inputs_layout)
        self.add_name = QLineEdit()
        add_form_inputs_layout.addWidget(self.add_name)
        self.add_value = QLineEdit()
        add_form_inputs_layout.addWidget(self.add_value)
        button = QPushButton("Add env var")
        add_form_inputs_layout.addWidget(button)
        button.clicked.connect(self._on_click_add)

        button = QPushButton("Reload file trees")
        add_form_inputs_layout.addWidget(button)
        button.clicked.connect(self._on_click_reload_helpers)

        add_form_layout.addRow("Add: ", add_form_inputs)

        self.refreshing = False
        self.refresh_table()
        self.main.show_now_or_later(self.table)


    def _os(self) -> bool:
        source = self.config.get(section="config", name="var_sub_source")
        return str(source).strip() == "env"

    def envs(self) -> dict:
        if self._os():
            return os.environ.items()
        else:
            ce = ConfigEnv(config=self.config)
            return ce.env

    def _delete_key(self, name:str) -> None:
        if self._os():
            if name in os.environ:
                del os.environ[name]
            self.main.state.set_env(name, None)
        else:
            env = self.envs()
            if name in env:
                del env[name]
            ConfigEnv(config=self.config).write_env_file(env)

    def _set_key(self, name:str, value:str) -> None:
        if self._os():
            os.environ[name] = value
            self.main.state.set_env(name, value)
        else:
            env = self.envs()
            env[name] = value
            ConfigEnv(config=self.config).write_env_file(env)

    def _has_key(self, name:str) -> bool:
        if self._os():
            return name in os.environ
        else:
            return name in self.envs()


    def _on_click_reload_helpers(self) -> None:
        #
        # we need to reload env vars, then reset stuff, esp. the right-side file trees
        # to do that we have to clear the clients out of box so when the trees reload
        # any clients needed have the right vars. and we need to prompt the user to save
        # if they have changed any config.
        #
        # load_state_and_cd is a heavy operation because it repopulates the rt-side
        # trees. can't think of a way around. we don't know any env vars impact the
        # trees so we can't be more discriminating about what we reload.
        #
        self.main.question_config_close()
        Box().empty_my_stuff()
        self.main.load_state_and_cd()

    def _enum(self):
        if self._os():
            return self.envs()
        else:
            return self.envs().items()

    def refresh_table(self) -> None:
        self.refreshing = True
        ffilter = self.filter_input.text()
        ffilter = ffilter if ffilter and ffilter.strip() != "" else None
        rows = {}
        for k, v in self._enum():
            if ffilter is not None:
                r = re.compile(ffilter)
                m = r.findall(k)
                if len(m) == 0:
                    continue
            rows[k] = v
        row = 0
        self.table.setRowCount(len(rows))
        for k, v in rows.items():
            ki = QTableWidgetItem(k)
            vi = QTableWidgetItem(v)
            self.table.setItem(row, 0, ki)
            self.table.setItem(row, 1, vi)
            row += 1
        self.refreshing = False

    def _on_click_update(self) -> None:
        self.refresh_table()

    def _on_click_add(self) -> None:
        #
        # add item
        #
        name = self.add_name.text()
        value = self.add_value.text()
        if value is None or value.strip() == "":
            self._delete_key(name)
        else:
            self._set_key(name, value)
        #
        # update table
        #
        self.refresh_table()

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if self.refreshing is True:
            return
        row = item.row()
        value = self.table.item(row, 1)
        if value is None:
            return
        new_text = item.text()
        key = self.table.item(row, 0)
        k = key.text()
        if new_text is None or new_text.strip() == "":
            if self._has_key(k):
                self._delete_key(k)
        else:
            self._set_key(k, new_text)
        self.refresh_table()

    def add_to_config(self, config) -> None:
        self.refresh_table()

    def populate(self):
        self.refresh_table()

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

