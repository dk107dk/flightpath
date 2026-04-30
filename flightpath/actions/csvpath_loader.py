import traceback

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QMessageBox

from csvpath import CsvPaths
from csvpath.util.nos import Nos

from flightpath.dialogs.load_paths_dialog import LoadPathsDialog


class CsvpathLoader:
    def __init__(self, *, main, parent):
        super().__init__()
        self.main = main
        self.my_parent = parent
        self.load_dialog = None

    def load_paths(self, path) -> None:
        self.load_dialog = LoadPathsDialog(
            main=self.main, path=path, parent=self.main.sidebar, loader=self
        )
        # When the dialog finishes, drop the reference
        self.load_dialog.finished.connect(lambda _: setattr(self, "load_dialog", None))
        self.main.show_now_or_later(self.load_dialog)

    def do_append_named_paths_load(self) -> None:
        self.do_load(overwrite=False)

    def do_overwrite_named_paths_load(self) -> None:
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
        self.main.welcome.update_run_button()

    def do_load_file(self, *, overwrite=True) -> None:
        template = None
        if self.load_dialog.template_ctl:
            template = self.load_dialog.template_ctl.text()
        if template is None:
            ...
        elif template.strip() == "":
            template = None
        elif not template.endswith(":run_dir"):
            self.load_dialog.setWindowFlag(Qt.WindowStaysOnTopHint, False)
            """
            meut.message2(
                parent=self.load_dialog,
                title="Incorrect Template",
                msg="A named-path group template must end in :run_dir",
            )
            """
            self.load_dialog.warning(
                title="Incorrect Template",
                msg="A named-path group template must end in :run_dir",
            )
            return
        named_paths_name = None
        if self.load_dialog.named_paths_name_ctl:
            named_paths_name = self.load_dialog.named_paths_name_ctl.text()
        if named_paths_name and named_paths_name.strip() == "":
            named_paths_name = None
        paths = self.main.csvpaths

        if paths.paths_manager.has_named_paths(named_paths_name):
            """
            meut.yesNo2(
                parent=self,
                title="Continue?",
                msg=(
                    "Are you sure you want to overwrite an existing named-paths group?"
                    if overwrite
                    else "Are you sure you want to append to an existing named-paths group?"
                ),
                callback=self._do_load_file,
                args={
                    "overwrite": overwrite,
                    "named_paths_name": named_paths_name,
                    "paths": self.main.csvpaths,
                    "template": template,
                },
            )
            """
            self.load_dialog.yesNo(
                title="Continue?",
                msg=(
                    "Are you sure you want to overwrite an existing named-paths group?"
                    if overwrite
                    else "Are you sure you want to append to an existing named-paths group?"
                ),
                callback=self._do_load_file,
                args={
                    "overwrite": overwrite,
                    "named_paths_name": named_paths_name,
                    "paths": self.main.csvpaths,
                    "template": template,
                },
            )
            return
        self._do_load_file(
            QMessageBox.Yes,
            overwrite=overwrite,
            named_paths_name=named_paths_name,
            paths=paths,
            template=template,
        )

    @Slot(int)
    def _do_load_file(
        self,
        answer: int,
        *,
        named_paths_name: str,
        paths: CsvPaths,
        overwrite: bool = True,
        template: str = None,
    ) -> None:
        if answer == QMessageBox.No:
            return
        #
        # if the named-paths name exists, warn the user that they are adding a named-path to the group
        #
        try:
            name = self.load_dialog.path
            name = "" if not name else name.strip()
            if Nos(name).isfile():
                ext = name[name.rfind(".") + 1 :]
                if ext in self.main.csvpath_config.get(
                    section="extensions", name="csvpath_files"
                ):
                    #
                    # added append=(not overwrite) to do an append when the form requires.
                    # however, atm, the append is only available on add_named_files(). the
                    # change to add append to add_named_paths_from_file() is done, but needs
                    # testing and a local release so we can use it. till then, this will
                    # break
                    #
                    # have to override the filesystem prohibit because it doesn't make sense
                    # here. we are all local file-based atm and also control config.
                    #
                    paths.config.set(
                        section="inputs", name="allow_local_files", value=True
                    )
                    ref = paths.paths_manager.add_named_paths_from_file(
                        name=named_paths_name,
                        file_path=name,
                        template=template,
                        append=(not overwrite),
                    )
                    if ref is None or str(ref).strip() == "":
                        """
                        meut.warning2(
                            parent=self.load_dialog,
                            msg="Cannot load file",
                            title="Cannot Load",
                        )
                        """
                        self.load_dialog.warning(
                            msg="Cannot load file", title="Cannot Load"
                        )
                        return
                else:
                    raise ValueError(f"Unknown file type: {name}")
            self.main.sidebar._renew_sidebars()
            self._delete_load_dialog()
        except Exception as e:
            print(traceback.format_exc())
            """
            meut.warning2(
                parent=self.load_dialog,
                title="Error",
                msg=f"Cannot load named-paths group: {e}",
            )
            """
            self.load_dialog.warning(
                msg=f"Cannot load named-paths group: {e}", title="Error"
            )

    def do_load_json(self) -> None:
        print("oad groupdef")
        paths = self.main.csvpaths
        #
        # not sure this hint is necessary or helpful. tbd.
        #
        self.load_dialog.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.load_dialog.show()
        #
        # warn the user that they are overwriting any existing named-path to the group.
        # this warning prompt must pop over the dialog, not under, or we get into problems.
        #
        msg = "Ok to overwrite any existing named-paths groups referenced in your JSON?"
        confirm = QMessageBox.question(
            self.main, "Load Paths", msg, QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.No:
            return

        name = self.load_dialog.path
        name = "" if not name else name.strip()
        ex = None
        msg = None
        try:
            lst = paths.paths_manager.add_named_paths_from_json(file_path=name)  #
            if paths.errors and len(paths.errors) > 0:
                es = [error.to_json() for error in paths.errors]
                """
                meut.errors2(
                    parent=self.my_parent,
                    msg="Errors during load",
                    title="Errors",
                    errors=es,
                )
                """
                self.load_dialog.load_errors(
                    msg="Errors during load", title="Errors", errors=es
                )
                return

            if lst is None or len(lst) == 0:
                """
                meut.warning2(
                    parent=self.load_dialog,
                    msg="Cannot load file",
                    title="Cannot Load",
                    callback=self._delete_load_dialog,
                )
                """
                self.load_dialog.warning(msg="Cannot load file", title="Cannot Load")
                return
        except Exception as e:
            msg = traceback.format_exc()
            print(msg)
            ex = e
        if ex is not None or paths.has_errors():
            ja = None
            if paths.has_errors():
                if paths.errors and len(paths.errors) > 0:
                    ja = []
                    for e in paths.errors:
                        ja.append(e.to_json())
            title = "Errors"
            if paths.errors is None:
                msg = f"There were errors: {ex}"
            elif len(paths.errors) == 1:
                msg = f"There was {len(paths.errors)} error"
                title = "Error"
            else:
                msg = f"There were {len(paths.errors)} errors"
            """
            meut.errors2(
                parent=self.load_dialog,
                msg=msg,
                title="Error",
                errors=ja,
                callback=self._delete_load_dialog,
            )
            """
            self.load_dialog.load_errors(msg=msg, title=title, errors=ja)
            return

        else:
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
        paths = self.main.csvpaths
        #
        # if the named-paths name exists, warn the user that they are adding a named-path to the group
        #
        if paths.paths_manager.has_named_paths(named_paths_name):
            msg = (
                "Are you sure you want to overwrite an existing named-paths group?"
                if overwrite
                else "Are you sure you want to append to an existing named-paths group?"
            )
            """
            meut.yesNo2(
                parent=self.load_dialog,
                title="Load Paths",
                msg=msg,
                callback=self._do_load_dir_answer,
                args={
                    "template": template,
                    "paths": paths,
                    "named_paths_name": named_paths_name,
                    "name": name,
                },
            )
            """
            self.load_dialog.yesNo(
                title="Load Paths",
                msg=msg,
                callback=self._do_load_dir_answer,
                args={
                    "template": template,
                    "paths": paths,
                    "named_paths_name": named_paths_name,
                    "name": name,
                },
            )
            return
        self._do_load_dir_answer(
            QMessageBox.Yes,
            paths=paths,
            named_paths_name=named_paths_name,
            template=template,
            name=name,
        )

    @Slot(int)
    def _do_load_dir_answer(
        self,
        answer,
        *,
        paths: CsvPaths,
        named_paths_name: str,
        name: str,
        template: str = None,
    ) -> None:
        #
        # atm, paths_manager gacks on "". this has been fixed in csvpath as of 507
        #
        if str(template).strip() in ["", "None"]:
            template = None
        lst = paths.paths_manager.add_named_paths_from_dir(
            name=named_paths_name, directory=name, template=template
        )
        if lst is None or len(lst) == 0:
            """
            meut.warning2(
                parent=self.load_dialog,
                msg="Cannot load directory.",
                title="Cannot Load",
                callback=self._do_load_dir_finish,
            )
            """
            self.load_dialog.warning(
                msg="Cannot load directory.",
                title="Cannot Load",
                callback=self._do_load_dir_finish,
            )
        else:
            self._do_load_dir_finish()
        #
        # have to check if the named-paths group has a definition file. if not
        # we need to create one.
        # -- handling this by adding a default option in CsvPath.
        #
        # def store_json_for_paths(self, name: NamedPathsName, definition: str) -> None:
        #

    def _do_load_dir_finish(self) -> None:
        self.main.sidebar._renew_sidebars()
        self._delete_load_dialog()

    def _delete_load_dialog(self):
        try:
            self.load_dialog.close()
            self.load_dialog.deleteLater()
            self.load_dialog = None
        except Exception:
            ...
