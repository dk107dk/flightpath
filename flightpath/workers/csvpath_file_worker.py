
from PySide6.QtCore import QObject, Signal, Slot, QRunnable
from PySide6.QtWidgets import QApplication
from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos
from pathlib import Path

class CsvpathFileWorkerSignals(QObject):
    finished = Signal(tuple)
    messages = Signal(str)


class CsvpathFileWorker(QRunnable):

    def __init__(self, filepath, main):
        super().__init__()
        self.main = main
        self.filepath = str(filepath)
        self.signals = CsvpathFileWorkerSignals()

    @Slot()
    def run(self):
        nos = Nos(self.filepath)
        if not nos.exists():
            raise RuntimeError("Path {filepath} cannot not exist")

        self.signals.messages.emit(QApplication.translate("DataWorker", "Reading file..."))
        data = None
        with DataFileReader(self.filepath) as file:
            data = file.source.read()
        self.signals.messages.emit(QApplication.translate("DataWorker", "Validating file..."))
        #
        # try running a CsvPath run to see if the file is basically valid csvpath?
        #
        self.signals.messages.emit(QApplication.translate("DataWorker", f"Opened: {self.filepath}" ))
        #
        # provide the errors?
        #
        self.signals.finished.emit((self.filepath, data, []))



