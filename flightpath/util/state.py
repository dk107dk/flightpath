
import os
import json
from pathlib import Path

from csvpath import CsvPaths
from csvpath.util.config import Config as CsvPath_Config
#from csvpath.util.nos import Nos

from flightpath.dialogs.pick_cwd_dialog import PickCwdDialog
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.examples_marshal import ExamplesMarshal

class State:

    def __init__(self):
        self._state_path = None

    @property
    def home(self) -> str:
        home = str(Path.home())
        print(f"state.home: home is: {home}")
        return home

    @property
    def state_path(self) -> str:
        if self._state_path is None:
            self._state_path = os.path.join(self.home, ".flightpath")
            if not os.path.exists(self._state_path):
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
        with open(statepath, mode="w", encoding="utf-8") as file:
            json.dump(state, file, indent=2)

    @state_path.setter
    def state_path(self, state_path:str) -> None:
        self._state_path = state_path

    @property
    def debug(self) -> str:
        return self.data.get("debug")

    @property
    def cwd(self) -> str:
        cwd = self.data.get("cwd")
        print(f"state.cwd: {cwd}")
        return cwd

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
        dialog.exec()

    def has_cwd(self) -> bool:
        return self.cwd is not None

    def load_state_and_cd(self, main) -> None:
        cwd = self.cwd
        #
        # to make things more clear, let's blow up if we don't have cwd at this point.
        #
        #print(f"state.load state & cd: cwd 1: {cwd}")
        #if cwd is None:
        #    cwd = self.home
        #print(f"state.load state & cd: cwd 2: {cwd}")
        os.chdir(cwd)
        configfile = f".{os.sep}config{os.sep}config.ini"
        new_project = not os.path.exists(configfile)
        #
        # if the dir has no config it is a new project. CsvPath Framework
        # will generate a config file. We need to add an examples folder
        # to help people get started. CsvPath Framework does not offer
        # examples.
        #
        if new_project:
            # ffr: we don't need this because Config creates a relative path by default
            #os.environ[CsvPath_Config.CSVPATH_CONFIG_FILE_ENV] = cwd
            #
            # this line is principlly to get the project dirs and files created
            # we can assume main.py will create its own CsvPaths and config for
            # its long term use.
            #
            CsvPaths().config
            examples = os.path.join(cwd, "examples")
            if os.path.exists(examples):
                ...
            else:
                os.makedirs(examples)
                em = ExamplesMarshal(main)
                em.add_examples(path=examples)
        else:
            ...





