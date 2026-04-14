import json
import traceback

from PySide6.QtCore import QRunnable

from csvpath.util.file_readers import DataFileReader
from csvpath import CsvPaths
from csvpath.util.box import Box

from flightpath.editable import EditStates
from .data_worker_signals import DataWorkerSignals


class JsonDataWorker(QRunnable):
    def __init__(self, filepath, main, editable=EditStates.EDITABLE):
        super().__init__()
        #
        #
        #
        self.filepath = filepath
        self.editable = editable
        self.signals = DataWorkerSignals()

    # @Slot()
    def run(self):
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
                s = None
                try:
                    s = file.source.read()
                    data = json.loads(s)
                except json.decoder.JSONDecodeError:
                    #
                    # we swallow the error. the json editor will open fine.
                    # the grid view will receive None and the user will have to
                    # fix in editor view.
                    #
                    print(traceback.format_exc())
                    data = s

        except Exception as e:
            print(traceback.format_exc())
            self.signals.messages.emit(f"  Erroring opening {self.filepath}")
            self.signals.finished.emit(("Error", e, None))
            return
        self.signals.messages.emit(f" Opened {str(self.filepath)}")
        self.signals.finished.emit((str(self.filepath), data, self.editable))
