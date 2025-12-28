
from PySide6.QtCore import QObject, Signal, Slot, QRunnable
from PySide6.QtWidgets import QApplication
from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos
from pathlib import Path

from flightpath.editable import EditStates
from .data_worker_signals import DataWorkerSignals

class CsvpathFileWorker(QRunnable):

    def __init__(self, filepath, main, editable=EditStates.EDITABLE):
        super().__init__()
        self.main = main
        self.filepath = str(filepath)
        self.editable = editable
        self.signals = DataWorkerSignals()

    def run(self):
        try:
            nos = Nos(self.filepath)
            if not nos.exists():
                raise RuntimeError(f"Path {self.filepath} does not exist")

            self.signals.messages.emit("Reading file...")
            data = None
            with DataFileReader(self.filepath) as file:
                data = file.source.read()
        except Exception as e:
            print(f"Error: {type(e)}: {e}")
            self.signals.messages.emit(f"  Erroring opening {self.filepath}")
            self.signals.finished.emit(("Error", e, None))
            return
        #
        # try running/parsing w/a CsvPath to chk file is basically valid CsvPath Language?
        #
        self.signals.messages.emit(f"Opened: {self.filepath}" )
        #
        # provide editable indicator
        #
        self.signals.finished.emit((self.filepath, data, self.editable))



