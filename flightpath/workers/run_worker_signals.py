from PySide6.QtCore import QObject, Signal


class RunWorkerSignals(QObject):
    finished = Signal(tuple)
    error = Signal(tuple)
    messages = Signal(str)
