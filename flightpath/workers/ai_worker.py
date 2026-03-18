
from PySide6.QtCore import QObject, Signal, QRunnable, Slot
from flightpath.workers.jobs.ai_job import AiJob

class AiWorkerSignals(QObject):
    turn = Signal(object)       # partial updates
    finished = Signal(object)   # final text
    error = Signal(str)         # error message


class AiWorker(QRunnable):
    def __init__(self, job: AiJob):
        super().__init__()
        self.job = job
        self.signals = AiWorkerSignals()

        self.job.on_turn_update = self.signals.turn.emit
        self.job.on_complete = self.signals.finished.emit
        self.job.on_error = self.signals.error.emit

    @Slot()
    def run(self):
        self.job.do_generate()
