#import sys
import os
#import re

from csvpath.util.nos import Nos
from csvpath.util.path_util import PathUtility as pathu

class SidebarFileRefMaker:

    def __init__(self, *, main, parent):
        super().__init__()
        self.main = main
        self.parent = parent

    def new_run_ref(self):
        ref = self._named_file_ref()
        return ref

    def _named_file_ref(self) -> str:
        index = self.parent.view.currentIndex()
        if not index.isValid():
            # could this ever happen?
            return
        path = self.parent.model.filePath(index)
        nos = Nos(path)
        if nos.isfile():
            return self._fingerprint_ref_for_path(path)
        name = self._named_file_name_for_path(path)
        if self._is_named_file_name(path):
            return name
        ref = self._ref_path_for_path(path)
        ref = ref.replace(".", "_")
        ref = f"${name}.files.{ref}:last"
        return ref

    def _is_named_file_name(self, path:str) -> bool:
        name = self._named_file_name_for_path(path)
        #
        # is name same as path minus inputs dir?
        #
        nfnpath = path[len(self._inputs)+1:]
        return name == nfnpath

    def _named_file_name_for_path(self, path:str) -> str:
        sep = pathu.sep(path)[0]
        name = path[len(self._inputs)+1:]
        if name.find(sep) == -1:
            return name
        name = name[0:name.find(sep)]
        return name

    def _ref_path_for_path(self, path:str) -> str:
        #
        # remove the inputs dir
        #
        name = path[len(self._inputs)+1:]
        #
        # remove the named-file name too
        #
        sep = pathu.sep(path)[0]
        name = name[name.find(sep) + 1:]
        return name

    def _fingerprint_ref_for_path(self, path:str) -> str:
        fingerprint = os.path.basename(path)
        sep = pathu.sep(path)[0]
        name = path[len(self._inputs)+1:]
        if name.find(sep) > -1:
            name = name[0:name.find(sep)]
        return f"${name}.files.{fingerprint}"

    @property
    def _inputs(self) -> str:
        return self.main.csvpath_config.get(section="inputs", name="files")




