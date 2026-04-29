import os
from typing import Callable

from PySide6.QtWidgets import QFileDialog, QWidget
from PySide6.QtCore import Slot

from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.config import Config
from csvpath.util.nos import Nos

from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.message_utility import MessageUtility as meut


class FileCollector:
    @classmethod
    def csvpaths_filter(cls, cfg: Config) -> str:
        exts = cfg.get(section="extensions", name="csvpath_files")
        ext_str = ""
        for e in exts:
            ext_str = f"{ext_str} *.{e}"
        return f"CsvPath Language files ({ext_str})"

    @classmethod
    def csvs_filter(cls, cfg) -> str:
        exts = cfg.get(section="extensions", name="csv_files")
        ext_str = ""
        for e in exts:
            ext_str = f"{ext_str} *.{e}"
        return f"Data files ({ext_str})"

    @classmethod
    def select_file(
        cls,
        *,
        parent: QWidget,
        cwd: str = None,
        title: str,
        file_type_filter: str,
        do_not_copy_if_in: bool = False,
        callback: Callable = None,
        args: dict = None,
    ) -> None:
        #
        # selects a single file. if the file is not in the project's folder tree it will be copied in.
        #
        # check if base copy-to is a file. if it is, user must select a dir in the
        # left-hand navigator.
        #
        if cwd is not None:
            nos = Nos(cwd)
            if nos.isfile():
                cwd = os.path.dirname(cwd)
                """
                meut.message2(
                    parent=parent,
                    msg="Please select a directory in the file browser",
                    title="Not a directory",
                )
                return
                """
        d = QFileDialog()
        d.setOptions(
            QFileDialog.Option.DontResolveSymlinks
            | QFileDialog.Option.ReadOnly
            | QFileDialog.Option.DontUseCustomDirectoryIcons
        )
        d.setFileMode(QFileDialog.FileMode.ExistingFile)
        d.setViewMode(QFileDialog.ViewMode.List)
        d.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        if file_type_filter:
            d.setNameFilter(file_type_filter)
        if title:
            d.setWindowTitle(title)
        the_path = None
        _ = d.exec()
        if _:
            paths = d.selectedFiles()
            the_path = paths[0]
            name = os.path.basename(the_path)

            if the_path.startswith(cwd) and do_not_copy_if_in is True:
                cls._select_file_complete(
                    (the_path, True),
                    the_path=the_path,
                    do_not_copy_in=True,
                    callback=callback,
                    args=args,
                    cwd=cwd,
                )
                return
            else:
                meut.input2(
                    parent=parent,
                    title="Copy into {cwd}",
                    msg="Enter a name for the copy:",
                    text=name,
                    callback=cls._select_file_complete,
                    args={
                        "cwd": cwd,
                        "the_path": the_path,
                        "callback": callback,
                        "args": args,
                    },
                )
                return

            """
            _ = the_path.startswith(cwd)
            if not _:
                name = os.path.basename(the_path)
                meut.input2(
                    parent=parent,
                    title="Copy into {cwd}",
                    msg="Enter a name for the copy:",
                    text=name,
                    callback=cls._select_file_complete,
                    args={
                        "cwd": cwd,
                        "the_path": the_path,
                        "callback": callback,
                        "args": args,
                    },
                )
                return
            else:
                meut.message2(
                    parent=parent,
                    title="In Project",
                    msg=f"{the_path} is already in the project",
                )
                return
            """
        #
        # calls back with the new path or None. you can choose to not
        # provide a callback if you're just picking and copying
        #
        if callback is None:
            return
        args = {} if args is None else args
        callback(the_path, **args)

    @classmethod
    @Slot(tuple)
    def _select_file_complete(
        self,
        t: tuple[str, bool],
        *,
        cwd: str,
        the_path: str,
        do_not_copy_in: bool = False,
        callback: Callable,
        args: dict = None,
    ) -> str:
        new_name, ok = t
        new_path = None
        if ok and new_name and do_not_copy_in is False:
            new_path = fiut.deconflicted_path(cwd, new_name)
            with DataFileReader(the_path, mode="rb") as the_file:
                with DataFileWriter(path=new_path, mode="wb") as new_file:
                    new_file.write(the_file.read())
        else:
            new_path = new_name
        if callback is None:
            return
        args = {} if args is None else args
        callback(new_path, **args)
