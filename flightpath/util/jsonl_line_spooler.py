import os
import json
import logging
from pathlib import Path

from .file_writers import DataFileWriter
from .nos import Nos
from .path_util import PathUtility as pathu



class JsonLineSpooler(LineSpooler):
    def __init__(
        self,
        *,
        path: str,
        delimiter: str = ",",
        quotechar: str = '"',
    ) -> None:
        self._path = path

    @property
    def path(self) -> str:
        if self._path is None:
            self._instance_data_file_path()
        return self._path

    @path.setter
    def path(self, p: str) -> None:
        p = pathu.resep(p)
        self._path = p

    def load_if(self) -> None:
        self.sink = self._open_file(self.path)

    def _open_file(self, path: str):
        dw = DataFileWriter(path=path, mode="w")
        dw.load_if()
        return dw.sink

    def append(self, line) -> None:
        if not self.sink:
            self.load_if()
        if not self.sink:
            msg = f"Cannot write to {self.path}"
            raise InputException(msg)
        self.sink.write(line)
        self._count += 1

    def bytes_written(self) -> int:
        try:
            i = FileInfo.info(self.path)
            if i and "bytes" in i:
                return i["bytes"]
            else:
                return -1
        except FileNotFoundError:
            return 0

    def close(self) -> None:
        try:
            if self.sink:
                self.sink.close()
                self.sink = None
                self.closed = True
        except Exception as ex:
            self.sink = None
            raise

