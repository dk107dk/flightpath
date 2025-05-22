
import os
import json
from pathlib import Path
from PySide6.QtWidgets import QMessageBox

from csvpath import CsvPaths
from csvpath.util.config import Config as CsvPath_Config
from csvpath.util.nos import Nos

from flightpath.dialogs.pick_cwd_dialog import PickCwdDialog
from flightpath.util.examples_marshal import ExamplesMarshal
from flightpath.util.os_utility import OsUtility as osut
from flightpath.util.file_utility import FileUtility as fiut

class State:
    #
    # home is a path, typically a full path
    # projects_home is a dirname
    # cwd is a dirname
    #
    # to find a project you stackup all three: f"{home}{projects_home}{cwd}
    #
    # in version one home was static (same), there was no projects_home and cwd
    # was a full path. anything remaining of that should be removed. the reason
    # for the switch was Apple's sandbox's silly way of handling/mixing container
    # home and user's traditional home, while manditating the use of the native
    # file picker dialog. untenable, but also results in something simpler and
    # probably better.
    #

    def __init__(self):
        self._state_path = None

    @property
    def home(self) -> str:
        #
        # the .flightpath file lives in the user's home dir (which may
        # be a sandbox container home dir)
        #
        home = str(Path.home())
        print(f"state.home: user home is: {home}")
        return home

    @property
    def projects_home(self) -> str:
        #
        # the default projects home is <home>/FlightPath. if there is a
        # directory at that location already we will use it and hope it is
        # what the user wants. typically it will be, but we don't fully
        # control what is there.
        #
        data = self.data
        home = data.get("projects_home")
        if home is None:
            print(f"state.project_home: no project home in state")
            home = "FlightPath"
            #
            # let's make sure projects home exists and the default project exists
            #
            nos = Nos(os.path.join(self.home, home))
            if not nos.exists():
                nos.makedirs()
            nos.path = os.path.join(home, "Default")
            if not nos.exists():
                nos.makedirs()
            #
            # save for later.
            #
            if data:
                print(f"state.project_home: setting project home in state")
                data["projects_home"] = home
                #
                # set the default project as cwd while we're at it.
                #
                data["cwd"] = os.path.join(home, "Default")
                nos = Nos(os.path.join(os.path.join(self.home, home), "Default"))
                if not nos.exists():
                    nos.makedirs()
                self.data = data
            else:
                print(f"state.project_home: cannot set project home in state")
        print(f"state.project_home: project home is: {home}")
        return home

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
            proj = "Default"
            nos = Nos(os.path.join(self.projects_home, proj))
            if not nos.exists():
                nos.makedirs()
            self.current_project = proj
        return proj

    @current_project.setter
    def current_project(self, proj:str) -> str:
        data = self.data
        data["current_project"] = proj
        self.data = data

    @property
    def state_path(self) -> str:
        #
        # state path is the location of .flightpath
        #
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
        # not doing this here. likely to cause problems.
        #
        #state["projects_home"] = self.projects_home
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
        return f"{home}{os.sep}{projs}{os.sep}{proj}"

        #cwd = self.data.get("cwd")
        #print(f"state.cwd: {cwd}")
        #return cwd

    @cwd.setter
    def cwd(self, cwd:str) -> None:
        #
        # still needed?
        #
        if osut.is_mac() and osut.is_sandboxed():
            ncwd = fiut.to_sandbox_path(cwd)
            if ncwd is None:
                #
                # warn. we don't have main so we cannot resurface the cdw picker.
                # that may not be bad. it is possible the user knows what they are
                # doing. it is also possible that this situation could never happen.
                #
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setWindowTitle("Unknown path")
                msg_box.setText(f"{cwd} is not within the app sandbox. This may be an issue.")
                msg_box.setStandardButtons(QMessageBox.Ok)
                msg_box.exec()
            else:
                cwd = ncwd

        proj = os.path.basename(cwd)
        projs = os.path.dirname(cwd)
        home = os.path.dirname(projs)
        projs = os.path.basename(projs)

        self.home = home
        self.current_project = proj
        self.projects_dir = projs

        """
        data = self.data
        data["cwd"] = cwd
        self.data = data
        """

    @property
    def data(self) -> dict:
        with open(self.state_path, mode="r", encoding="utf-8") as file:
            return json.load(file)

    @data.setter
    def data(self, state:dict) -> None:
        with open(self.state_path, mode="w", encoding="utf-8") as file:
            state = json.dump(state, file)

    def pick_cwd(self, main) -> None:
        # NO LONGER USED
        #
        # the caller has to check our has_cwd() method again
        # to find out if we succeeded. fine, i think.
        #
        #dialog = PickCwdDialog(main)
        #dialog.exec()
        ...

    def has_cwd(self) -> bool:
        return self.cwd is not None

    def load_state_and_cd(self, main) -> None:
        cwd = self.cwd
        #
        # we may want to check writability since we are still giving folks the
        # ability to easily set their projects home, but since we're not file
        # picking, we're starting within the container (if sandboxed) and we use
        # the home as the root of the projects dir, we may be able to just not.
        # the main worry would be people setting a ../../xyz type path. but that's
        # not likely and probably not our problem.
        #
        """
        if cwd and not fiut.is_writable_dir(cwd):
            #
            # create a workable cwd, if possible, otherwise alert user
            #
            ncwd = fiut.to_sandbox_path(cwd)
            if ncwd is None:
                #
                # warn
                #
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setWindowTitle("Path is not writable")
                msg_box.setText(f"{cwd} is not writable. Use the config panel to pick another directory for your work.")
                msg_box.setStandardButtons(QMessageBox.Ok)
                msg_box.exec()
                cwd = None
            else:
                self.cwd = ncwd
        """
        #
        # for now, let's blow up if we're missing a cwd
        #
        nos = Nos(cwd)
        if not nos.exists():
            nos.makedirs()

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
            #
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





