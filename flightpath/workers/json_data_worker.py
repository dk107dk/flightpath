import json

from PySide6.QtCore import Qt, QAbstractTableModel, QObject, Signal, Slot, QRunnable
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableView, QLabel, QApplication

from csvpath.util.file_readers import DataFileReader

from .data_worker_signals import DataWorkerSignals

class JsonDataWorker(QRunnable):

    def __init__(self, filepath, main, editable=True):
        super().__init__()
        self.main = main
        self.filepath = filepath
        self.editable = editable
        self.signals = DataWorkerSignals()

    @Slot()
    def run(self):
        self.signals.messages.emit("Reading file...")
        try:
            data = []
            with DataFileReader(str(self.filepath)) as file:
                data = json.load(file.source)
        except Exception as e:
            print(f"Error: {type(e)}: {e}")
            self.signals.messages.emit(f"  Erroring opening {self.filepath}")
            self.signals.finished.emit(("Error", e, None))
            return
        self.signals.messages.emit(f" Opened {str(self.filepath)}")
        self.signals.finished.emit(( str(self.filepath), data, self.editable))



