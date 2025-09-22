from PySide6.QtCore import QObject, Signal

class PreCacheWorkerSignals(QObject):
    finished = Signal(tuple)
    messages = Signal(str)



