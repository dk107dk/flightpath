
from PySide6.QtCore import QObject, Signal, QRunnable, Slot
from flightpath.workers.jobs.ai_generate_csvpath_job import AiGenerateCsvpathJob

class AiGenerateCsvpathWorkerSignals(QObject):
    turn = Signal(object)       # partial updates
    finished = Signal(object)   # final text
    error = Signal(str)         # error message


class AiGenerateCsvpathWorker(QRunnable):
    def __init__(self, job: AiGenerateCsvpathJob):
        super().__init__()
        self.job = job
        self.signals = AiGenerateCsvpathWorkerSignals()

        self.job.on_turn_update = self.signals.turn.emit
        self.job.on_complete = self.signals.finished.emit
        self.job.on_error = self.signals.error.emit

    @Slot()
    def run(self):
        self.job.do_generate()
