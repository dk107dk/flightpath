
import os
import json
from pathlib import Path
from PySide6.QtWidgets import QMessageBox

from csvpath import CsvPaths
from csvpath.util.config import Config as CsvPath_Config
from csvpath.util.nos import Nos

from flightpath.util.examples_marshal import ExamplesMarshal
from flightpath.util.os_utility import OsUtility as osut
from flightpath.util.file_utility import FileUtility as fiut

class State:

    DEFAULT_PROJECT_NAME = "Default"
    DEFAULT_PROJECTS_DIR = "FlightPath"
    STATE_FILE_NAME = ".flightpath"

    #
    # home is the path to user's home dir. not stored in state.
    # projects_home is a dirname
    # current_project is a dirname
    #
    # to find a project you stackup all three: {home}{projects_home}{current_project}
    #

    def __init__(self):
        self._state_path = None

    @property
    def home(self) -> str:
        #
        # the state file lives in the user's home dir (which may
        # be a sandbox container home dir)
        #
        home = str(Path.home())
        return home

    @property
    def projects_home_path(self) -> str:
        return os.path.join(self.home, self.projects_home)

    @property
    def projects_home(self) -> str:
        #
        # the default projects home is <home>/FlightPath. if there is a
        # directory at that location already we will use it and hope it is
        # what the user wants. typically it will be, but we don't fully
        # control what is there.
        #
        data = self.data
        projs = data.get("projects_home")
        if projs is None:
            projs = self.DEFAULT_PROJECTS_DIR
            #
            # let's make sure projects home exists and the default project exists
            #
            projects_dir = os.path.join(self.home, projs)
            nos = Nos(projects_dir)
            if not nos.exists():
                nos.makedirs()
            nos.path = os.path.join(projects_dir, self.DEFAULT_PROJECT_NAME)
            if not nos.exists():
                nos.makedirs()
            #
            # save for later.
            #
            if data:
                data["projects_home"] = projs
                #
                # make the default project while we're at it.
                #
                nos = Nos(os.path.join(projects_dir, self.DEFAULT_PROJECT_NAME))
                if not nos.exists():
                    nos.makedirs()
                self.data = data
            else:
                ...
                #print(f"state.project_home: cannot set project home in state")
        return projs

    @projects_home.setter
    def projects_home(self, home:str) -> None:
        data = self.data
        if home is None and data.get("projects_home") is not None:
            del data["projects_home"]
        else:
            data["projects_home"] = home
        self.data = data

    @property
    def current_project(self) -> str:
        proj = self.data.get("current_project")
        if proj is None:
            proj = self.DEFAULT_PROJECT_NAME
            nos = Nos(os.path.join(self.projects_home_path, proj))
            if not nos.exists():
                nos.makedirs()
            self.current_project = proj
        elif proj.strip() == "":
            proj = self.DEFAULT_PROJECT_NAME
        elif proj.find(os.sep) > -1:
            proj = proj[0:proj.find(os.sep)]
        return proj

    @current_project.setter
    def current_project(self, proj:str) -> str:
        data = self.data
        data["current_project"] = proj
        self.data = data

    @property
    def state_path(self) -> str:
        #
        # state path is the location of the state file
        #
        if self._state_path is None:
            self._state_path = os.path.join(self.home, self.STATE_FILE_NAME)
            print(f"State file path: {self._state_path}")
            if not os.path.exists(self._state_path):
                import getpass
                current_user = getpass.getuser()
                self._create_new_state_file(self._state_path)
        return self._state_path

    def _create_new_state_file(self, statepath:str) -> None:
        state = {}
        #
        # TODO: this is a brittle way to setup the config forms integrations.
        # hard to change & disconnected.
        #
        state["integrations"] = [
            "ckan", "default", "openlineage", "scripts", "sftp", "slack", "sql", "sqlite"
        ]
        #
        # not doing this here. likely to cause problems.
        #
        #state["projects_home"] = self.projects_home
        #
        # default cwd has to be writable. the macos app package isn't so we
        # use the user's home dir.
        #
        with open(statepath, mode="w", encoding="utf-8") as file:
            json.dump(state, file, indent=4)

    @state_path.setter
    def state_path(self, state_path:str) -> None:
        print(f"Setting state path to {state_path}")
        self._state_path = state_path

    @property
    def debug(self) -> str:
        #
        # this can probably go away. we can just run from the cmdline w/in MacOS in the
        # .app package. maybe wait till we know if windows has something similar.
        #
        return self.data.get("debug")

    @property
    def cwd(self) -> str:
        #
        # cwd is a single project that we're working out of. it must be directly below
        # projects_dir. if cwd changes we must clear the cwd and start over.
        #
        home = self.home
        projs = self.projects_home
        proj = self.current_project
        if proj is None or proj.strip() == "":
            proj = self.DEFAULT_PROJECT_NAME
        return f"{home}{os.sep}{projs}{os.sep}{proj}"

    @property
    def data(self) -> dict:
        with open(self.state_path, mode="r", encoding="utf-8") as file:
            return json.load(file)

    @data.setter
    def data(self, state:dict) -> None:
        with open(self.state_path, mode="w", encoding="utf-8") as file:
            json.dump(state, file, indent=4)

    def has_cwd(self) -> bool:
        return self.cwd is not None

    def load_env(self) -> bool:
        data = self.data
        env = data.get("env")
        if env is None:
            env = {}
            data["env"] = env
            self.data = data
        for k, v in env.items():
            try:
                os.environ[k] = v
            except ValueError as e:
                print(f"Error setting {k} to {v}: {e}")

    def set_env(self, k:str, v:str) -> None:
        data = self.data
        env = data.get("env")
        if env is None:
            env = {}
            data["env"] = env
        if v is None:
            if k in env:
                del env[k]
        else:
            env[k] = v
        self.data = data

    def load_state_and_cd(self, main) -> None:
        #
        # we have been loading the .flightpath env vars at startup and project change.
        # it's quick and fine. most often won't be needed.
        #
        self.load_env()
        #
        #
        #
        cwd = self.cwd
        nos = Nos(cwd)
        #
        # is this a problem? when would cwd not exist?
        #
        if not nos.exists():
            nos.makedirs()
        os.chdir(cwd)
        configfile = f".{os.sep}config{os.sep}config.ini"
        new_project = not os.path.exists(configfile)
        #
        #
        #
        config = CsvPaths().config
        #
        # we were not doing this, but it seems like the right place and time.
        #
        main.csvpath_config = config
        """
        #
        # invalidate the config form so it will rebuild
        #
        if main.main_layout:
            main.main_layout.widget(2).ready = False
        if main.config:
            main.config.config_panel.ready = False
            #main.config.config_panel.populate_all_forms()
        """

        #
        # remember: setting config.configpath triggers a reload.
        #
        config.configpath = os.path.join(cwd, "config", "config.ini")
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
            config.set(section="config", name="path", value=os.path.join(cwd, "config", "config.ini") )
            config.set(section="config", name="allow_var_sub", value="yes" )
            config.set(section="config", name="var_sub_source", value=os.path.join(cwd, "config", "env.json") )
            config.set(section="cache", name="path", value=os.path.join(cwd, "cache") )
            config.set(section="logging", name="log_file", value=os.path.join(cwd, "logs", "csvpath.log") )
            config.set(section="inputs", name="files", value=os.path.join(cwd, "inputs", "named_files") )
            config.set(section="inputs", name="csvpaths", value=os.path.join(cwd, "inputs", "named_paths") )
            config.set(section="results", name="archive", value=os.path.join(cwd, "archive") )
            config.set(section="results", name="transfers", value=os.path.join(cwd, "transfers") )
            config.set(section="sqlite", name="db", value=os.path.join(cwd, "archive", "csvpath.db") )
            config.set(section="sql", name="connection_string", value="" )
            config.save_config()
            examples = os.path.join(cwd, "examples")
            if os.path.exists(examples):
                ...
            else:
                os.makedirs(examples)
                em = ExamplesMarshal(main)
                em.add_examples(path=examples)






