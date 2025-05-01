import os
from csvpath import CsvPaths

class PathsRefCreator:

    def __init__(self, *, main, named_paths=None) -> None:
        self.main = main
        self.named_paths = named_paths
        self.paths = CsvPaths()

    def _has_name(self, name:str) -> bool:
        try:
            self.paths.paths_manager.has_named_paths(name)
        except Exception as e:
            return False

    def get(self) -> str:
        name = self.named_paths
        if name is None:
            raise ValueError("Name cannot be None")
        mgr = self.paths.paths_manager
        #
        # user clicked on top level so we go with the simple name
        #
        if self._has_name(name):
            return name
        ref = ""
        cwd = self.main.state.cwd
        if name.startswith(cwd):
            name = name[len(cwd)+1:]
        #
        # likewise, user clicked on top level and we have cwd + name
        #
        if self._has_name(name):
            return name
        inputs = self.paths.config.get(section="inputs", name="csvpaths")
        if name.startswith(inputs):
            name = name[len(inputs)+1:]
        if self._has_name(name):
            return name
        #
        # the top level was cwd + paths inputs + named-path name. so
        # we return just the name
        #
        file = os.path.dirname(name)
        if not file or file.strip() == "":
            return name
        ret = f"${file}.csvpaths.0:from"
        return ret

