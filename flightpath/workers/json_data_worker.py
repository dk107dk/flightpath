import json

from PySide6.QtCore import Qt, QAbstractTableModel, QObject, Signal, Slot, QRunnable
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableView, QLabel, QApplication

from csvpath.util.file_readers import DataFileReader
from csvpath import CsvPaths
from csvpath.util.box import Box


from .data_worker_signals import DataWorkerSignals

class JsonDataWorker(QRunnable):

    def __init__(self, filepath, main, editable=True):
        super().__init__()
        #
        #
        #
        self.main = main
        self.filepath = filepath
        self.editable = editable
        self.signals = DataWorkerSignals()

    @Slot()
    def run(self):
        print(f"JsonDataWorker: run: reading {self.filepath}")
        self.signals.messages.emit("Reading file...")
        try:
            data = []
            #
            # this is a hack workaround for sftp. a change has been made in csvpath so
            # this code can be deleted after the next update after 546.
            #
            config = CsvPaths().config
            Box().add(Box.CSVPATHS_CONFIG, config)
            #
            #
            #
            with DataFileReader(str(self.filepath)) as file:
                data = json.load(file.source)
            print(f"JsonDataWorker: run: data: {len(data)}: {data}")
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            print(f"Error: {type(e)}: {e}")
            self.signals.messages.emit(f"  Erroring opening {self.filepath}")
            self.signals.finished.emit(("Error", e, None))
            return
        self.signals.messages.emit(f" Opened {str(self.filepath)}")
        self.signals.finished.emit(( str(self.filepath), data, self.editable))

        print(f"JsonDataWorker: run: done reading {self.filepath}. found: \n{json.dumps(data, indent=4)}")


