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
        self.signals.messages.emit(QApplication.translate("DataWorker", "Reading file..."))
        data = []
        with DataFileReader(str(self.filepath)) as file:
            data = json.load(file.source)
        errors = []
        self.signals.messages.emit(QApplication.translate("DataWorker", f" Opened {str(self.filepath)}"))
        self.signals.finished.emit(( str(self.filepath), data, self.editable))



