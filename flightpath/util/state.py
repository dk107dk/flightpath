
import os
import json
from pathlib import Path

from csvpath import CsvPaths
from csvpath.util.config import Config as CsvPath_Config
from csvpath.util.nos import Nos

from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.examples_marshal import ExamplesMarshal

class State:

    def __init__(self):
        self._state_path = None
        self._home = str(Path.home())

    @property
    def state_path(self) -> str:
        if self._state_path is None:
            self._state_path = os.path.join(self._home, ".flightpath")
        return self._state_path

    @state_path.setter
    def state_path(self, state_path:str) -> None:
        self._state_path = state_path

    @property
    def cwd(self) -> str:
        cwd = self.data.get("cwd")
        return cwd

    @cwd.setter
    def cwd(self, cwd:str) -> None:
        data = self.data
        data["cwd"] = cwd
        self.data = data

    @property
    def data(self) -> dict:
        state = None
        if os.path.exists(self.state_path):
            with open(self.state_path, mode="r", encoding="utf-8") as file:
                state = json.load(file)
        if not state or state.get("cwd") is None:
            if not state:
                state = {}
                #
                # TODO: this is a brittle way to setup the config forms integrations.
                # hard to change & disconnected.
                #
                state["integrations"] = [
                    "ckan", "default", "marquez", "scripts", "sftp", "sftpplus", "slack", "sql", "sqlite"
                ]
            #
            # default cwd has to be writable. the macos app package isn't so we
            # use the user's home dir.
            #
            state["cwd"] = self._home
            with open(self.state_path, mode="w", encoding="utf-8") as file:
                json.dump(state, file, indent=2)
        return state

    @data.setter
    def data(self, state:dict) -> None:
        if os.path.exists(self.state_path):
            with open(self.state_path, mode="w", encoding="utf-8") as file:
                state = json.dump(state, file)
        else:
            print(f"Error: path does not exist: {self.state_path}")

    def has_state(self) -> bool:
        nos = Nos(self.state_path)
        if not nos.exists():
            return False
        return True

    def pick_cwd(self, main) -> None:
        #
        # the caller has to check our has_cwd() method again
        # to find out if we succeeded. fine, i think.
        #
        from flightpath.dialogs.pick_cwd_dialog import PickCwdDialog
        dialog = PickCwdDialog(main)
        dialog.show_dialog()

    def has_cwd(self) -> bool:
        has = self.has_state()
        if not has:
            return False
        with open(self.state_path, mode="r", encoding="utf-8") as file:
            state = json.load(file)
        if "cwd" in state:
            return True
        return False

    def load_state_and_cd(self, main) -> None:
        data = self.data
        cwd = data.get("cwd")
        if cwd is None:
            cwd = self._home
        else:
            try:
                os.chdir(cwd)
                #
                # if the dir has no config it is a new project. CsvPath Framework
                # will generate a config file. We need to add an examples folder
                # to help people get started. CsvPath Framework does not offer
                # examples.
                #
                new_project = not os.path.exists(f".{os.sep}config/config.ini")
                main.csvpath_config = CsvPaths().config
                if new_project:
                    examples = os.path.join(cwd, "examples")
                    nos = Nos(examples)
                    if not nos.exists():
                        nos.makedirs()
                    em = ExamplesMarshal(main)
                    em.add_examples(path=examples)
            except Exception as e:
                print(f"Error setting cwd: {type(e)}: {e}")




