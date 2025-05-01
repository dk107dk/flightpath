import os
import json
from pathlib import Path

from flightpath.util.file_utility import FileUtility as fiut
from csvpath import CsvPaths
from csvpath.util.config import Config as CsvPath_Config

class State:

    def __init__(self):
        #self._state = None
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

    def load_state_and_cd(self, main) -> None:
        data = self.data
        cwd = data.get("cwd")
        if cwd is None:
            print(f"Error: no cwd in state. Using home.")
            cwd = self._home
        else:
            try:
                os.chdir(cwd)
                main.csvpath_config = CsvPaths().config
            except Exception as e:
                print(f"Error setting cwd: {type(e)}: {e}")
        #self.main.startup()




