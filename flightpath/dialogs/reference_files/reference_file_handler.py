import os
import json

from PySide6.QtGui import QClipboard, QStandardItemModel, QStandardItem, QAction
from PySide6.QtCore import Qt,Slot # pylint: disable=E0611
from PySide6.QtWidgets import QApplication

from csvpath import CsvPaths
from csvpath.util.path_util import PathUtility as pathu
from csvpath.util.nos import Nos

from flightpath.util.log_utility import LogUtility as lout
from flightpath.util.tabs_utility import TabsUtility as tabu
from flightpath.util.message_utility import MessageUtility as meut
from flightpath.editable import EditStates

class ReferenceFileHandler:

    #===== INIT ================

    def __init__(self, *, parent):
        self.dialog = parent
        self.main = self.dialog.main
        self.paths = CsvPaths()

    #===== UTIL METHODS ================

    def _item(self, row) -> str:
        item_index = self.dialog.model.index(row, 0)
        item = self.dialog.model.itemFromIndex(item_index)
        t = item.text()
        return t

    def _type(self) -> str:
        datatype = self.dialog.datatype.currentText()
        return datatype

    def _results_root(self) -> str:
        return self.paths.config.get(section="results", name="archive")

    def _files_root(self) -> str:
        return self.paths.config.get(section="inputs", name="files")

    def _trim_results_root(self, path)-> str:
        path = path[len(self._results_root())+1:]
        return path

    def _trim_files_root(self, path)-> str:
        path = path[len(self._files_root())+1:]
        return path

    def _named_file_name(self, path) -> str:
        n = self._trim_files_root(path)
        sep = pathu.sep(path)
        n = n[0:n.find(sep[0])]
        return n

    def _named_results_name(self, path) -> str:
        n = self._trim_results_root(path)
        sep = pathu.sep(path)
        n = n[0:n.find(sep[0])]
        return n

    def _named_file_home(self, path) -> str:
        home = self.paths.file_manager.named_file_home(self._named_file_name(path))
        return home

    def _named_results_home(self, path) -> str:
        name = self._named_results_name(path)
        home = self.paths.results_manager.get_named_results_home(name)
        return home

    def _named_file_manifest_path(self, path) -> str:
        path = os.path.join(self._named_file_home(path), "manifest.json")
        return path

    def _named_results_manifest_path(self, path) -> str:
        path = os.path.join(path, "manifest.json")
        return path

    def _is_files(self) -> bool:
        return self._type() == "files"

    def _is_results(self) -> bool:
        return self._type() == "results"

    #===== OPEN RUN_DIR ================

    @Slot(tuple)
    def _show_run_dir(self, row:int) -> None:
        t = self._item(row)
        try:
            sidebar = self.main.sidebar_rt_bottom
            view = sidebar.view
            model = sidebar.model
            path = self._trim_results_root(t)
            parts = pathu.parts(path)
            item = sidebar.model.root_item
            for part in parts:
                for i, ii in enumerate(item.child_items):
                    data = ii.data(0)
                    if data.path.endswith(part):
                        idx = model.createIndex(i, 0, ii)
                        view.expand(idx)
                        item = ii
                        break
        except Exception as e:
            import traceback
            print( traceback.format_exc())
            print(f"Error in _show_run_dir: {type(e)}: {e}")

    #===== COPY PATH ================

    def _copy_path(self, row) -> None:
        t = self._item(row)
        clipboard = QApplication.instance().clipboard()
        clipboard.setText(t)

    #===== OPEN MANIFEST ================

    def _show_manifest(self, row) -> None:
        if self._is_files():
            self._show_named_file_manifest(row)
        else:
            self._show_results_manifest(row)

    def _show_results_manifest(self, row) -> None:
        t = self._item(row)
        root = self._results_root()
        sep = pathu.sep(root)
        #
        # :all:first.hello world:data
        #
        path = t
        if t.endswith(f"{sep[0]}data.csv"):
            path = t[0:len(t) - 9]
        elif t.endswith(f"{sep[0]}unmatched.csv"):
            path = t[0:len(t) - 14]
        path = f"{path}{sep[0]}manifest.json"
        nos = Nos(path)
        if not nos.exists():
            meut.message(title="Manifest Not Found", msg=f"The named-results manifest was not found at {t}")
        else:
            self._show_run_dir(row)
            worker = self.main.read_validate_and_display_file_for_path(
                path,
                editable=EditStates.NO_SAVE_NO_CTX
            )

    def _show_named_file_manifest(self, row) -> None:
        t = self._item(row)
        path = self._named_file_manifest_path(t)
        nos = Nos(path)
        if not nos.exists():
            meut.message(title="Manifest Not Found", msg=f"The named-file manifest was not found at {path}")
        else:
            worker = self.main.read_validate_and_display_file_for_path(path, editable=EditStates.NO_SAVE_NO_CTX)
            worker.signals.finished.connect(lambda: self._display_file_entry_in_manifest(t))

    def _display_file_entry_in_manifest(self, path:str) -> None:
        #
        # the manifest is now open. we need to expand to the entry for the item.
        #
        mani = self.paths.file_manager.get_manifest(self.named_x_name.currentText())
        fingerprint = os.path.basename(path)
        fingerprint = fingerprint[0:fingerprint.rfind(".")]
        i = 0
        for i, entry in enumerate(mani):
            if entry["fingerprint"] == fingerprint:
                break
        index = w[1].view.model().index(i, 0)
        w[1].view.setCurrentIndex(index)
        w[1].view.setExpanded(index, True)

    #===== OPEN NAMED FILE ================

    def _open_origin_file(self, row) -> None:
        t = self._item(row)
        mpath = self._named_results_manifest_path(t)
        mani = None
        from csvpath.util.file_readers import DataFileReader
        with DataFileReader(mpath) as file:
            mani = json.load(file.source)
        if "actual_data_file" in mani:
            file = mani["actual_data_file"]
            self.main.read_validate_and_display_file_for_path(file, editable=EditStates.NO_SAVE_NO_CTX)
        else:
            file = mani["named_file_path"]
            self.main.read_validate_and_display_file_for_path(file, editable=EditStates.NO_SAVE_NO_CTX)

    def _open_files_file(self, row) -> None:
        t = self._item(row)
        self.main.read_validate_and_display_file_for_path(t, editable=EditStates.NO_SAVE_NO_CTX)
        self._display_named_file_in_tree(t)

    def _display_named_file_in_tree(self, path:str) -> None:
        sidebar = self.main.sidebar_rt_top
        view = sidebar.view
        model = sidebar.model
        parts = pathu.parts(path)
        item = sidebar.model.root_item
        for part in parts:
            for i, ii in enumerate(item.child_items):
                data = ii.data(0)
                if data.path.endswith(part):
                    idx = model.createIndex(i, 0, ii)
                    view.expand(idx)
                    item = ii
                    break

    #===== OPEN RESULTS DATA FILE ================

    def _open_results_file(self, row) -> None:
        t = self._item(row)
        self.main.read_validate_and_display_file_for_path(t, editable=EditStates.NO_SAVE_NO_CTX)
        self._display_results_file_in_tree(t)

    def _display_results_file_in_tree(self, path:str) -> None:
        sidebar = self.main.sidebar_rt_bottom
        view = sidebar.view
        model = sidebar.model
        parts = pathu.parts(path)
        item = sidebar.model.root_item
        for part in parts:
            for i, ii in enumerate(item.child_items):
                data = ii.data(0)
                if data.path.endswith(part):
                    idx = model.createIndex(i, 0, ii)
                    view.expand(idx)
                    item = ii
                    break


