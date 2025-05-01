import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QWidget
)

from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.config import Config

from flightpath.util.file_utility import FileUtility as fiut

class FileCollector:

    @classmethod
    def csvpaths_filter(cls, cfg:Config) -> str:
        exts = cfg.csvpath_file_extensions
        ext_str = ""
        for e in exts:
            ext_str = f"{ext_str} *.{e}"
        return f"CsvPath Language files ({ext_str})"

    @classmethod
    def csvs_filter(cls, cfg) -> str:
        exts = cfg.csv_file_extensions
        ext_str = ""
        for e in exts:
            ext_str = f"{ext_str} *.{e}"
        return f"Data files ({ext_str})"

    @classmethod
    def select_file(cls, *, parent:QWidget, cwd:str, title:str, filter:str) -> str:
        #
        # selects a single file. if the file is not in the project's folder tree it will be copied in.
        #
        d = QFileDialog()
        d.setOptions(QFileDialog.Option.DontUseNativeDialog)
        d.setFileMode(QFileDialog.FileMode.ExistingFile)
        if filter:
            d.setNameFilter(filter)
        if title:
            d.setWindowTitle(title)
        the_path = None
        if d.exec():
            paths = d.selectedFiles()
            the_path = paths[0]
            if not the_path.startswith(cwd):
                name = os.path.basename(the_path)
                new_name, ok = QInputDialog.getText(parent, "Copy into project", "Enter a name for the copy:", text=name)
                if ok and new_name:
                    new_path = fiut.deconflicted_path(cwd, new_name)
                    with DataFileReader(the_path) as the_file:
                        with DataFileWriter(path=new_path) as new_file:
                            new_file.write(the_file.read())
                    the_path = new_path
        return the_path


