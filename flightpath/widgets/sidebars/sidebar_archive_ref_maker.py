#import sys
import os
import json
import re

from flightpath.dialogs.new_run_dialog import NewRunDialog

from csvpath.util.nos import Nos
from csvpath import CsvPaths
from csvpath.managers.paths.paths_registrar import PathsRegistrar
from csvpath.util.path_util import PathUtility as pathu
from csvpath.util.config import Config
from csvpath.util.file_readers import DataFileReader

class SidebarArchiveRefMaker:

    def __init__(self, *, main, parent):
        super().__init__()
        self.main = main
        self.parent = parent


    def _new_run(self):
        index = self.parent.view.currentIndex()
        named_paths = self._named_paths_for_index(index=index)
        named_file = self._named_file_for_index(archive=self._archive, index=index)
        #
        # let's try to get the file
        #
        self.new_run_dialog = NewRunDialog(parent=self.parent, named_paths=named_paths, named_file=named_file)
        #
        # check for templates
        #
        npn = self._named_paths_for_index(index)
        t = CsvPaths().paths_manager.get_template_for_paths(npn)
        if t:
            self.new_run_dialog.template = t
            self.new_run_dialog.template_ctl.setText(t)
        #
        #
        #
        self.new_run_dialog.show()

    def _repeat_run(self):
        index = self.parent.view.currentIndex()
        named_paths, named_file = self._get_rerun_references(index)
        self.new_run_dialog = NewRunDialog(parent=self.parent, named_paths=named_paths, named_file=named_file)
        #
        # check for templates
        #
        npn = self._named_paths_for_index(index)
        t = CsvPaths().paths_manager.get_template_for_paths(npn)
        if t:
            self.new_run_dialog.template = t
            self.new_run_dialog.template_ctl.setText(t)
        #
        #
        #
        self.new_run_dialog.show()

    #
    #
    # ---------------------------
    # new run support
    #

    def _named_paths_for_index(self, index) -> str:
        named_paths = None
        path = self.parent.model.filePath(index)
        if not path:
            return ""
        path = path[len(self._archive) + 1:]
        sep = pathu.sep(path)[0]
        if path.find(sep) > -1:
            named_paths = path[0:path.find(sep)]
        else:
            named_paths = path
        return named_paths

    def _named_file_for_index(self, *, archive:str, index) -> str:
        named_file = None
        path = self.parent.model.filePath(index)
        m = re.search(r"^(.*\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(?:_\d)?)", path)
        d = None
        if m is not None:
            d = m.group(0)
        if d is not None:
            mani = os.path.join( d, "manifest.json")
            mani = os.path.join(archive, mani)
            nos = Nos(mani)
            j = {}
            if nos.exists():
                with DataFileReader(mani) as file:
                    j = json.load(file.source)
            named_file = j.get("named_file_name")
        return named_file

    #
    #
    # ---------------------------
    # rerun support
    #

    @property
    def _archive(self) -> str:
        return self.main.csvpath_config.get(section="results", name="archive")

    def _find_run_dir(self, path:str) -> str:
        run_dir = None
        m = re.search(r"^(.*\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(?:_\d)?)", path)
        if m is not None:
            run_dir = m.group(0)
        return run_dir

    def _is_named_path_dir(self, path:str) -> bool:
        sep = "/" if path.find("/") > -1 else "\\"
        name = path[len(self._archive)+1:]
        if name.find(sep) == -1:
            return name
        name = name[0:name.find(sep)]
        maybe = f"{self._archive}{sep}{name}"
        return maybe == path

    def _named_path_from_path(self, path:str) -> str:
        sep = "/" if path.find("/") > -1 else "\\"
        np = path[len(self._archive)+1:]
        if np.find(sep) == -1:
            return np
        np = np[0:np.find(sep)]
        return np

    def _use_named_path_name(self, path) -> str:
        name = self._named_path_from_path(path)
        run_dir = self._find_run_dir(path)
        if run_dir and path.endswith(run_dir):
            return name
        if self._is_named_path_dir(path):
            return name
        return None

    def _named_paths_reference_for_path(self, path:str) -> str:
        name = self._named_path_from_path(path)
        if self._use_named_path_name(path) is not None:
            return name
        reg = PathsRegistrar(CsvPaths())
        mp = reg.manifest_path(name)
        mani = reg.get_manifest(mp)
        amani = mani[len(mani)-1]
        ids = amani.get("named_paths_identities")
        index = 0
        identity = None
        for i, _ in enumerate(ids):
            if path.find(_) > -1:
             index = i
             identity = _
             break
        return f"${name}.csvpaths.{identity}:from"

    def _get_rerun_references(self, index) -> tuple[str,str]:
        path = self.parent.model.filePath(index)
        named_paths = self._named_paths_reference_for_path(path)
        #
        # named_file
        #
        named_file = self._named_file_reference_for_path(path)
        #
        # return as tuple
        #
        return (named_paths, named_file)

    def _named_file_reference_for_path(self, path:str) -> str:
        print("\n")
        d = self._find_run_dir(path)
        mani = ""
        if d is None:
            npn = self._named_path_from_path(path)
            mani = f"{self._archive}/{npn}/manifest.json"
            mani = pathu.resep(mani)
        else:
            mani = f"{d}/manifest.json"
            mani = pathu.resep(mani)
        nos = Nos(mani)
        j = None
        if nos.exists():
            with DataFileReader(mani) as file:
                j = json.load(file.source)
        if j is None:
            mani = f"{self._archive}/manifest.json"
            mani = pathu.resep(mani)
            with DataFileReader(mani) as file:
                j = json.load(file.source)
            run_dir = None
            j.reverse()
            for m in j:
                if m["run_home"].startswith(path):
                    run_home = m["run_home"]
                    break
            mani = f"{run_home}/manifest.json"
            mani = pathu.resep(mani)
            with DataFileReader(mani) as file:
                j = json.load(file.source)
        #
        # j must exist now, but what if it doesn't?
        #
        fingerprint = j.get("named_file_fingerprint")
        named_file = j.get("named_file_name")
        return f"{named_file}.files.{fingerprint}"



