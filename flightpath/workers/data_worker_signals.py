from PySide6.QtCore import QObject, Signal

class DataWorkerSignals(QObject):
    finished = Signal(tuple)
    messages = Signal(str)



