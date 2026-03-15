import traceback
import os
from PySide6.QtCore import QObject, Signal, Slot, QRunnable, QThreadPool, QThread
from PySide6.QtWidgets import QApplication
from csvpath import CsvPaths
from csvpath.util.nos import Nos
from .precache_worker_signals import PreCacheWorkerSignals

class PreCacheWorker(QRunnable):

    def __init__(self, cwd:str, *, main):
        super().__init__()
        self.main = main
        self.cwd = cwd
        self.signals = PreCacheWorkerSignals()

    def run(self):
        try:
            #
            # the project directory
            #
            csvpaths = self.main.csvpaths
            csvpaths.config.set(section="cache", name="path", value=f"{self.cwd}{os.sep}cache")
            csvpaths.config.set(section="cache", name="use_cache", value=f"yes")
            cacher = csvpaths.file_manager.lines_and_headers_cacher
            files = Nos(self.cwd).listdir(files_only=True, recurse=True)
            if files:
                self.signals.messages.emit(f"Precaching files")
                for file in files:
                    #
                    # just taking .csv means missing any *.tsv, etc. but it also
                    # keeps us from attempting excel files. excel should work fine
                    # but it is one more testing concern -- and we don't have an
                    # obvious way to handle multiple worksheets.
                    #
                    if os.path.dirname(file).endswith(f"{os.sep}cache"):
                        continue
                    if file.lower().endswith(".csv"):
                        self.signals.messages.emit(f"Precaching {file}")
                        try:
                            cacher.get_new_line_monitor(file)
                        except Exception as e:
                            print(traceback.format_exc())
                            self.signals.finished.emit(f"Precaching error in {file}")
        except Exception as e:
            print(traceback.format_exc())
            self.signals.finished.emit("A precaching error occured")
            return
        self.signals.finished.emit("Done precaching files")



