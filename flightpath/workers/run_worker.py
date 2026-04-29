import traceback
from datetime import datetime
from PySide6.QtCore import QRunnable, QCoreApplication
from .run_worker_signals import RunWorkerSignals


class RunException(Exception): ...


class RunWorker(QRunnable):
    def __init__(
        self,
        *,
        method: str,
        named_paths_name: str,
        named_file_name: str,
        template: str,
        csvpaths,
    ) -> None:
        super().__init__()
        #
        # need a new csvpaths because a) we don't encourage reusing them; although, it
        # is possible, and b) the listeners in the accordian require separate hook-ups.
        #
        self.csvpaths = csvpaths
        self.method = method
        self.named_paths_name = named_paths_name
        self.named_file_name = named_file_name
        self.template = template
        self.signals = RunWorkerSignals()
        self._item = None

    @property
    def item(self):
        return self._item

    @item.setter
    def item(self, item) -> None:
        self._item = item

    def run(self):
        self.signals.messages.emit(
            f"Running file {self.named_file_name} against {self.named_paths_name}"
        )
        paths = self.csvpaths
        #
        # we listen for events as well as using emit() so we want a certain
        # setup.
        #
        e = paths.config.get(section="errors", name="csvpaths")
        es = []
        es.append("collect")
        if "print" in e:
            es.append("print")
        if "raise" in e:
            es.append("raise")
        if "stop" in e:
            es.append("stop")
        if "fail" in e:
            es.append("fail")
        paths.config.set(section="errors", name="csvpaths", value=",".join(es))

        #
        # do run on paths
        #
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
                }
            )
            #
            # exp.
            #
            # removing csvpaths from the emit because it causes race condition that seems to have resulted in a crash
            # not sure who uses it, if anyone.
            #
            # ^^^^ got it. the run status dialog uses it to get the current line and total lines from the current
            # matcher.
            #
            #                     "csvpaths": paths,

            ref = None
            try:
                ref = a(
                    pathsname=self.named_paths_name,
                    filename=self.named_file_name,
                    template=self.template,
                )
            except Exception as ex:
                msg = str(ex)
                #
                # atm, the most workable status update is for us to raise our own error
                # and also pass it to our listener.
                #
                # in a perfect world the csvpaths would raise the error and our existing
                # listener that we use for run events would catch it.
                #
                # however, csvpaths doesn't always raise exceptions in a controlled way.
                # e.g. if a run is setup incorrectly and never starts it is likely to raise
                # an exeception regardless of error policy on the grounds that it is a)
                # irrecoverable, and b) a development problem that needs to be fixed by the
                # user before deployment.
                #
                # all ^^^^ is subject to change!
                #
                # also, we need csvpaths to better support dynamic external listeners. atm
                # run events are supported, but others not. and it's too hard to set up.
                #
                paths.error_manager.handle_error(source=paths, msg=msg)
                self.item.metadata_update(paths.errors[0])
                #
                # emit the error that main will catch for _display_error. that does not
                # update the item.
                #
                self.signals.error.emit((msg, paths))
                self.signals.messages.emit("Run failed")
                print(traceback.format_exc())
                QCoreApplication.processEvents()
            else:
                self.signals.messages.emit(f"Completed run {ref}")
                self.signals.finished.emit((ref, paths))
        except Exception as ex:
            print(traceback.format_exc())
            self.signals.error.emit((str(ex), paths))
            self.signals.messages.emit("Run failed")
        finally:
            self.main = None
