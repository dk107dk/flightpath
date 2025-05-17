
import os
import json
from pathlib import Path

from csvpath import CsvPaths
from csvpath.util.config import Config as CsvPath_Config
from csvpath.util.nos import Nos

from flightpath.dialogs.pick_cwd_dialog import PickCwdDialog
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
            nos = Nos(self._state_path)
            if not nos.exists():
                self._create_new_state_file(self._state_path)
        return self._state_path

    def _create_new_state_file(self, statepath:str) -> None:
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
        #state["cwd"] = self._home
        with open(statepath, mode="w", encoding="utf-8") as file:
            json.dump(state, file, indent=2)

    @state_path.setter
    def state_path(self, state_path:str) -> None:
        self._state_path = state_path

    @property
    def cwd(self) -> str:
        cwd = self.data.get("cwd")
        return cwd

    @property
    def debug(self) -> str:
        return self.data.get("debug")

    @cwd.setter
    def cwd(self, cwd:str) -> None:
        data = self.data
        data["cwd"] = cwd
        self.data = data

    @property
    def data(self) -> dict:
        with open(self.state_path, mode="r", encoding="utf-8") as file:
            return json.load(file)

    @data.setter
    def data(self, state:dict) -> None:
        with open(self.state_path, mode="w", encoding="utf-8") as file:
            state = json.dump(state, file)

    def pick_cwd(self, main) -> None:
        #
        # the caller has to check our has_cwd() method again
        # to find out if we succeeded. fine, i think.
        #
        dialog = PickCwdDialog(main)
        dialog.show_dialog()

    def has_cwd(self) -> bool:
        state = self.data
        if "cwd" in state:
            return True
        return False

    def load_state_and_cd(self, main) -> None:
        cwd = self.cwd
        if cwd is None:
            cwd = self._home
        try:
            os.chdir(cwd)
            new_project = not os.path.exists(f".{os.sep}config{os.sep}config.ini")
            #
            # if the dir has no config it is a new project. CsvPath Framework
            # will generate a config file. We need to add an examples folder
            # to help people get started. CsvPath Framework does not offer
            # examples.
            #
            if new_project:
                #
                # this line is principlly to get the project dirs and files created
                # we can assume main.py will create its own CsvPaths and config for
                # its long term use.
                #
                main.csvpath_config = CsvPaths().config
                examples = os.path.join(cwd, "examples")
                nos = Nos(examples)
                if not nos.exists():
                    nos.makedirs()
                    em = ExamplesMarshal(main)
                    em.add_examples(path=examples)
        except Exception as e:
            print(f"Error setting cwd: {type(e)}: {e}")




