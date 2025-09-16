import os
from PySide6.QtCore import QObject, Signal, Slot, QRunnable
from PySide6.QtWidgets import QApplication
from csvpath import CsvPaths
from csvpath.util.nos import Nos

class PreCacheWorker(QRunnable):

    def __init__(self, main):
        super().__init__()
        self.main = main

    @Slot()
    def run(self):
        try:
            #
            # the project directory
            #
            cwd = self.main.state.cwd
            csvpaths = CsvPaths()
            csvpaths.config.set(section="cache", name="path", value=f"{self.main.state.cwd}{os.sep}cache")
            csvpaths.config.set(section="cache", name="use_cache", value=f"yes")
            cacher = csvpaths.file_manager.lines_and_headers_cacher
            files = Nos(cwd).listdir(files_only=True, recurse=True)
            for file in files:
                #
                # just taking .csv means missing any *.tsv, etc. but it also
                # keeps us from attempting excel files. that should work fine
                # but it is one more testing concern -- and we don't have an
                # obvious way to handle multiple worksheets.
                #
                if os.path.dirname(file).endswith(f"{os.sep}cache"):
                    continue
                if file.lower().endswith(".csv"):
                    print(f"PreCacheWorker: caching {file}")
                    cacher.get_new_line_monitor(file)
            #
            # not sure this is needed or useful, but it may be helpful at the margin.
            #
            self.main.sidebar.threadpool = None
        except Exception as e:
            print(f"Error in precache worker: {type(e)}: {e}")
            import traceback
            print(traceback.format_exc())
            return



