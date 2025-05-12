
from PySide6.QtCore import QObject, Signal, Slot, QRunnable
from PySide6.QtWidgets import QApplication
from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos
from pathlib import Path

from .data_worker_signals import DataWorkerSignals

class CsvpathFileWorker(QRunnable):

    def __init__(self, filepath, main, editable=True):
        super().__init__()
        self.main = main
        self.filepath = str(filepath)
        self.editable = editable
        self.signals = DataWorkerSignals()

    @Slot()
    def run(self):
        nos = Nos(self.filepath)
        if not nos.exists():
            raise RuntimeError("Path {filepath} cannot not exist")

        self.signals.messages.emit(QApplication.translate("DataWorker", "Reading file..."))
        data = None
        with DataFileReader(self.filepath) as file:
            data = file.source.read()
        #
        # try running/parsing w/a CsvPath to chk file is basically valid CsvPath Language?
        #
        self.signals.messages.emit(QApplication.translate("DataWorker", f"Opened: {self.filepath}" ))
        #
        # provide editable indicator
        #
        self.signals.finished.emit((self.filepath, data, self.editable))



