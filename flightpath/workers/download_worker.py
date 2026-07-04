import os

from PySide6.QtCore import QObject, QRunnable, Signal

from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter


class DownloadSignals(QObject):
    finished = Signal(bool, str)


class DownloadWorker(QRunnable):
    """Downloads a remote file to a local project path using DataFileReader/DataFileWriter."""

    def __init__(self, *, uri: str, local_path: str) -> None:
        super().__init__()
        if not uri:
            raise ValueError("uri cannot be empty")
        if not local_path:
            raise ValueError("local_path cannot be empty")
        self.setAutoDelete(False)
        self.uri = uri
        self.local_path = local_path
        self.signals = DownloadSignals()

    def run(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.local_path), exist_ok=True)
            mode = "wb" if self.uri.endswith(".xlsx") else "w"
            with DataFileReader(self.uri) as reader:
                with DataFileWriter(path=self.local_path, mode=mode) as writer:
                    writer.write(reader.read())
            self.signals.finished.emit(True, self.local_path)
        except Exception as e:
            self.signals.finished.emit(False, str(e))
