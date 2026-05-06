import os

from PySide6.QtWidgets import QFileDialog, QWidget

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
        cwd: str,
        title: str,
        file_type_filter: str,
        do_not_copy_if_in=True,
        check_cwd: bool = True,
        **kwargs,
    ) -> str:
        #
        # WARNING: this class has had trouble on MacOS picking files outside the sandbox
        # and copying them into the sandbox. it worked in the first 3 releases but breaks
        # (gracefully, in a does-nothing way) in the 4th release.
        #
        #
        # selects a single file. if the file is not in the project's folder tree it will
        # be copied in.
        #
        # have to be careful about the use of the meut methods. a̶p̶p̶l̶e̶'̶s̶ ̶s̶a̶n̶d̶b̶o̶x̶ ̶r̶e̶q̶u̶i̶r̶e̶s̶
        # u̶s̶ ̶t̶o̶ ̶s̶t̶a̶y̶ ̶o̶n̶ ̶#̶ ̶o̶n̶e̶ ̶t̶h̶r̶e̶a̶d̶,̶ ̶s̶o̶ ̶w̶e̶ ̶h̶a̶v̶e̶ ̶t̶o̶ ̶e̶x̶e̶c̶(̶)̶ ̶n̶o̶t̶ ̶s̶h̶o̶w̶(̶)̶
        #
        # after many attempts, i'm at a loss as to how to get the mac sandbox to work again.
        # that said it is probably not a threads issue; more likely the change in code-
        # signing we did between release 3 and 4, even though i can't see what change could
        # have that effect. regardless, we used it in exactly 2 places and one of those uses
        # needed to be removed anyway, so we're just working around the sandbox for now.
        #
        # check if base copy-to is a file. if it is, user must select a dir in the
        # left-hand navigator.
        #
        nos = Nos(cwd)
        if nos.isfile():
            meut.message2(
                parent=parent,
                msg="Please select a directory in the file browser",
                title="Not a directory",
            )
            return
        d = QFileDialog()
        d.setOptions(
            QFileDialog.Option.DontResolveSymlinks
            | QFileDialog.Option.ReadOnly
            | QFileDialog.Option.DontUseCustomDirectoryIcons
            # exp -- this is terrible. avoid if possible!
            # | QFileDialog.Option.DontUseNativeDialog
        )
        print(f"FileCollector: setting directory: {cwd}")
        if not cwd.endswith("/"):
            cwd = f"{cwd}/"
        d.setDirectory(cwd)
        d.setFileMode(QFileDialog.FileMode.ExistingFile)
        d.setViewMode(QFileDialog.ViewMode.List)
        d.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        if file_type_filter:
            d.setNameFilter(file_type_filter)
        if title:
            d.setWindowTitle(title)
        the_path = None
        if d.exec():
            paths = d.selectedFiles()
            the_path = paths[0]
            if check_cwd is True and not the_path.startswith(cwd):
                meut.warning2(
                    parent=parent,
                    title="Unavailable",
                    msg="You must pick a file within the project",
                )
                return
            if do_not_copy_if_in is True:
                return the_path
            name = os.path.basename(the_path)
            new_name = os.path.basename(name)
            if True:
                new_path = fiut.deconflicted_path(cwd, new_name)
                print(f"FileCollector: select_file: the_path: {the_path}")
                print(f"FileCollector: select_file: new_path: {new_path}")
                with DataFileReader(the_path, mode="rb") as the_file:
                    with DataFileWriter(path=new_path, mode="wb") as new_file:
                        new_file.write(the_file.read())
                the_path = new_path
        return the_path
