import traceback
from datetime import datetime

from PySide6.QtCore import QRunnable
from .run_worker_signals import RunWorkerSignals


class RunWorker(QRunnable):
    def __init__(
        self,
        *,
        method: str,
        named_paths_name: str,
        named_file_name: str,
        template: str,
        main,
    ) -> None:
        super().__init__()
        self.main = main
        #
        # need a new csvpaths because a) we don't encourage reusing them; although, it
        # is possible, and b) the listeners in the accordian require separate hook-ups.
        #
        self.csvpaths = main.new_csvpaths()
        self.method = method
        self.named_paths_name = named_paths_name
        self.named_file_name = named_file_name
        self.template = template
        self.signals = RunWorkerSignals()

    # @Slot()
    def run(self):
        self.signals.messages.emit(
            f"Running file {self.named_file_name} against {self.named_paths_name}"
        )
        #
        # do run on paths
        #
        paths = self.csvpaths
        a = getattr(paths, self.method)
        if a is None:
            #
            # not sure how this could happen
            #
            return
        try:
            #
            # we'd like to get the run_dir and exact start time, at least. maybe
            # other things too. we do that by adding the accordian item as a
            # results listener. cid = str(id(csvpath)) links item, csvpaths
            # and listener. and we want the csvpaths to use to get info re: the
            # state of any/all of the set of csvpath held by the running csvpaths.
            #
            self.signals.started.emit(
                {
                    "id": str(id(self)),
                    "cid": str(id(self.csvpaths)),
                    "start_time": str(datetime.now()),
                    "csvpaths": paths,
                }
            )
            ref = a(
                pathsname=self.named_paths_name,
                filename=self.named_file_name,
                template=self.template,
            )
            self.signals.messages.emit(f"Completed run {ref}")
            self.signals.finished.emit((ref, paths))
        except Exception as ex:
            self.signals.messages.emit(f"Error in run: {ex}")
            self.signals.error.emit((str(ex), paths))
            print(traceback.format_exc())
        self.main = None
