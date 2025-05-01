import os
import re

from csvpath import CsvPaths
from csvpath.util.path_util import PathUtility as pathu

class FileRefCreator:

    def __init__(self, *, main, named_file=None) -> None:
        self.main = main
        self.named_file = named_file
        self.paths = CsvPaths()

    def get(self) -> str:
        name = self.named_file
        if name is None:
            raise ValueError("Name cannot be None")
        #
        # check if name is just a simple name
        #
        if self._has_name(name):
                return name
        print(f"FileRefC: 1 name: {name}")
        ref = ""
        #
        # check if we're cwd + simple name. if so, just remove cwd.
        #
        cwd = self.main.state.cwd
        if name.startswith(cwd):
            name = name[len(cwd)+1:]
        if self._has_name(name):
            return name
        print(f"FileRefC: 2 name: {name}")
        #
        # check if we're cwd + the file staging area + simple name.
        # cwd is gone, so just remove file staging.
        #
        inputs = self.paths.config.get(section="inputs", name="files")
        if name.startswith(inputs):
            inputs = name[0:len(inputs)]
            name = name[len(inputs)+1:]
        if self._has_name(name):
            return name
        #
        # we may be looking for a more specific place lower down.
        # if so, we need to separate the simple name from the
        # progressive match.
        #
        ps = pathu.parts(name)
        file = ps[0]
        name = name[len(file)+1:]
        print(f"FileRefC: 3 name: {name}, file: {file}")
        if not self._has_name(file):
            #
            # not sure how this could happen since we're driven off
            # the mouse click, but fwiw
            #
            return None
        print(f"FileRefC: 4 name: {name}")
        name_one = name[len(file)+1:]
        #
        # if we're below a "." extension, we need to replace the "."
        # w/"_"
        #
        #
        # if we're going down to the level of the hashname we want to loose the extension
        #
        name_one = None
        h = self._get_hash(name)
        if h:
            name_one = h
        else:
            name_one = name.replace(".", "_")
            name_one = f"{name_one}:last"
        ret = f"${file}.files.{name_one}"
        print(f"FileRefC: done: {ret}")
        return ret

    def _get_hash(self, name:str) -> str:
        #
        # like:
        #   $zip.files.odes_csv/71990e87a06c2d8e13299485a43f6001c7589bc6677153f7fab30c796db0a6e3.csv
        #
        m = re.search(r"^.*([a-fA-F0-9]{64}).*$", name)
        if m:
            h = m.group(1)
            return h
        return None

    def _has_name(self, name) -> bool:
        mgr = self.paths.file_manager
        try:
            b = self.paths.file_manager.has_named_file(name)
            return b
        except Exception:
            return False



