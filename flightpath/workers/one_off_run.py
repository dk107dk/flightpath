import os
from PySide6.QtCore import QObject, Signal, Slot, QRunnable
from PySide6.QtWidgets import QApplication
from csvpath import CsvPath
from .run_worker_signals import RunWorkerSignals


#
# this worker does a one-off CsvPath run from the CsvPath viewer panel.
# it is different from run worker because it uses CsvPath, not CsvPaths.
# the assumption is that it is for dev/test work before deploy to prod.
#
class OneOffRunWorker(QRunnable):

    def __init__(self, *,
        csvpath:CsvPath,
        csvpath_str:str,
        printer
    ) -> None:
        super().__init__()
        self.csvpath = csvpath
        self.csvpath_str = csvpath_str
        self.printer = printer
        self.signals = RunWorkerSignals()

    def run(self):
        self.signals.messages.emit("Doing test run")
        path = self.csvpath
        lines = None

        try:
            lines = path.collect()
            self.signals.messages.emit(f"Test run complete. Matched {len(lines)} line{'s' if len(lines) != 1 else ''}.")
        except Exception as ex:
            import traceback
            print( traceback.format_exc())
            self.csvpath.logger.error(ex)
            self.signals.messages.emit(f"Test run failed")
        self.signals.finished.emit( (self.csvpath, self.csvpath_str, lines, self.printer ) )

