import json

from PySide6.QtCore import Qt, QAbstractTableModel, QObject, Signal, Slot, QRunnable
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableView, QLabel, QApplication

from csvpath.util.file_readers import DataFileReader

class DataWorkerSignals(QObject):
    finished = Signal(tuple)
    messages = Signal(str)

class JsonDataWorker(QRunnable):

    def __init__(self, filepath, main):
        super().__init__()
        self.main = main
        self.filepath = filepath
        self.signals = DataWorkerSignals()
        self.sample_size = 5

    @Slot()
    def run(self):
        self.signals.messages.emit(QApplication.translate("DataWorker", "Reading file..."))
        data = []
        with DataFileReader(str(self.filepath)) as file:
            data = json.load(file.source)

        self.signals.messages.emit(QApplication.translate("DataWorker", "Validating file..."))
        errors = []
        self.signals.messages.emit(QApplication.translate("DataWorker", "Read and Validation finished."))
        self.signals.finished.emit(( str(self.filepath), data, errors))



