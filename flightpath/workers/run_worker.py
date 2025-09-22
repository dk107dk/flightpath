import os
from PySide6.QtCore import QObject, Signal, Slot, QRunnable
from PySide6.QtWidgets import QApplication
from csvpath import CsvPaths
from .run_worker_signals import RunWorkerSignals


class RunWorker(QRunnable):

    def __init__(self, *,
        method:str,
        named_paths_name:str,
        named_file_name:str,
        template:str
    ) -> None:
        super().__init__()
        self.csvpaths = CsvPaths()
        self.method = method
        self.named_paths_name = named_paths_name
        self.named_file_name = named_file_name
        self.template = template
        self.signals = RunWorkerSignals()

    @Slot()
    def run(self):
        self.signals.messages.emit("Running file {self.named_file_name} against {self.named_paths_name}")
        #
        # do run on paths
        #
        paths = self.csvpaths
        a = getattr(paths, self.method)
        if a is None:
            #
            # not sure how this could happen
            #
            return
        ref = a(pathsname=self.named_paths_name, filename=self.named_file_name, template=self.template)
        self.signals.messages.emit(f"Completed run {ref}")
        self.signals.finished.emit( (ref, paths))



