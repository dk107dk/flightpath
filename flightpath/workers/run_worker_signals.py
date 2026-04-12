from PySide6.QtCore import QObject, Signal


class RunWorkerSignals(QObject):
    started = Signal(tuple)
    finished = Signal(tuple)
    error = Signal(tuple)
    messages = Signal(str)
