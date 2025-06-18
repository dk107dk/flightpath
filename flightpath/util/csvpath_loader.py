import os
#from pathlib import Path

from PySide6.QtWidgets import QMessageBox

from csvpath import CsvPaths
from csvpath.util.nos import Nos

from flightpath.dialogs.load_paths_dialog import LoadPathsDialog

class CsvpathLoader:

    def __init__(self, main):
        super().__init__()
        self.main = main
        self.load_dialog = None


    def load_paths(self, path) -> None:
        self.load_dialog = LoadPathsDialog(path=path, parent=self.main.sidebar, loader=self)
        self.load_dialog.show_dialog()

    def do_append_named_paths_load(self) ->None:
        self.do_load(overwrite=False)

    def do_overwrite_named_paths_load(self) ->None:
        self.do_load(overwrite=True)

    def do_load(self, *, overwrite=True) -> None:
        name = self.load_dialog.path
        name = "" if not name else name.strip()
        if name.endswith(".json"):
            self.do_load_json()
        elif Nos(name).isfile():
            self.do_load_file(overwrite=overwrite)
        else:
            self.do_load_dir(overwrite=overwrite)

    def do_load_file(self, *, overwrite=True) -> None:
        template = None
        if self.load_dialog.template_ctl:
            template = self.load_dialog.template_ctl.text()
        if template is not None or template.strip() == "":
            template = None
        named_paths_name = None
        if self.load_dialog.named_paths_name_ctl:
            named_paths_name = self.load_dialog.named_paths_name_ctl.text()
        if named_paths_name and named_paths_name.strip() == "":
            named_paths_name = None
        paths = CsvPaths()
        #
        # if the named-paths name exists, warn the user that they are adding a named-path to the group
        #
        if paths.paths_manager.has_named_paths(named_paths_name):
            if not self._check_ok_to_proceed(overwrite):
                return
        name = self.load_dialog.path
        name = "" if not name else name.strip()
        if Nos(name).isfile():
            ext = name[name.rfind(".")+1:]
            if ext in self.main.csvpath_config.csvpath_file_extensions:
                #
                # added append=(not overwrite) to do an append when the form requires.
                # however, atm, the append is only available on add_named_files(). the
                # change to add append to add_named_paths_from_file() is done, but needs
                # testing and a local release so we can use it. till then, this will
                # break
                #
                print(f"loadertemplatex: {template}")
                paths.paths_manager.add_named_paths_from_file(
                    #name=None,
                    name=named_paths_name,
                    file_path=name,
                    template=template,
                    append=(not overwrite)
                )
            else:
                raise ValueError(f"Unknown file type: {name}")
        self.main.sidebar._renew_sidebars()
        self._delete_load_dialog()

    def do_load_json(self) -> None:
        paths = CsvPaths()
        #
        # warn the user that they are overwriting any existing named-path to the group
        #
        msg = "Ok to overwrite any existing named-paths groups referenced in your JSON?"
        confirm = QMessageBox.question( self.main, "Load Paths", msg, QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.No:
            return
        name = self.load_dialog.path
        name = "" if not name else name.strip()
        paths.paths_manager.add_named_paths_from_json(file_path=name)
        self.main.sidebar._renew_sidebars()
        self._delete_load_dialog()

    def do_load_dir(self, *, overwrite=True) -> None:
        template = None
        if self.load_dialog.template_ctl:
            template = self.load_dialog.template_ctl.text()
        if template and template.strip() == "":
            template = None
        named_paths_name = None
        if self.load_dialog.named_paths_name_ctl:
            named_paths_name = self.load_dialog.named_paths_name_ctl.text()
        if named_paths_name and named_paths_name.strip() == "":
            named_paths_name = None
        name = self.load_dialog.path
        paths = CsvPaths()
        #
        # if the named-paths name exists, warn the user that they are adding a named-path to the group
        #
        if paths.paths_manager.has_named_paths(named_paths_name):
            if not self._check_ok_to_proceed(overwrite):
                return
        paths.paths_manager.add_named_paths_from_dir(name=named_paths_name, directory=name, template=template)
        self._renew_sidebars()
        self._delete_load_dialog()

    def _check_ok_to_proceed(self, overwrite:bool) -> bool:
        msg = (
                "Are you sure you want to overwrite an existing named-paths group?"
                if overwrite else
                "Are you sure you want to append to an existing named-paths group?"
        )
        confirm = QMessageBox.question(
            self.main.sidebar,
            "Load Paths",
            msg,
            QMessageBox.Yes | QMessageBox.No,
        )
        confirm == QMessageBox.Yes
        return confirm

    def _delete_load_dialog(self):
        self.load_dialog.close()
        self.load_dialog.deleteLater()
        self.load_dialog = None


