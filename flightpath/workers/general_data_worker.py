import csv
import random
import traceback

from PySide6.QtCore import Qt, QObject, Signal, Slot, QRunnable
from PySide6.QtWidgets import QApplication

from csvpath.util.file_readers import DataFileReader
from csvpath.matching.util.expression_utility import ExpressionUtility as exut

from flightpath.widgets.panels.data_viewer import DataViewer
from flightpath.widgets.toolbars.data_toolbar import DataToolbar
from flightpath.editable import EditStates
from .data_worker_signals import DataWorkerSignals

class GeneralDataWorker(QRunnable):

    def __init__(
        self,
        filepath,
        main,
        *,
        rows:str,
        sampling:str,
        delimiter:str=None,
        quotechar:str=None,
        editable:bool=False
    ):
        super().__init__()
        self.main = main
        self.filepath = filepath
        self.signals = DataWorkerSignals()
        self.sample_size:int = self._rows(rows) if rows else 50
        self.sampling = sampling if sampling else DataToolbar.FIRST_N
        self.line_take = 0
        self.lines_to_take:list[int] = None
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.editable = editable

    def _rows(self, s) -> int:
        if s == "All lines":
            return -1
        i = exut.to_int(s)
        if not isinstance(i, int):
            i = 50
        return i

    def accept_line(self, line_num:int, line:list[str]) -> bool:
        #
        # -1 means "All lines"
        # None means stop here
        #
        if self.sample_size == -1:
            return True
        #
        # if we've taken the number of lines requested we're done
        #
        if self.sample_size > -1 and self.line_take >= self.sample_size:
            return None
        #
        # if sampling is every line and we are collecting all lines
        #
        if (self.sampling == DataToolbar.FIRST_N):
            self.line_take += 1
            return True
        elif self.sampling == DataToolbar.RANDOM_0:
            if random.randint(0,1) % 2 == 0:
                self.line_take += 1
                return True
            return False
        elif self.sampling == DataToolbar.RANDOM_ALL:
            if line_num == self.lines_to_take[len(self.lines_to_take)-1]:
                self.line_take += 1
                removed = self.lines_to_take.pop()
                return True
        return False

    def run(self):
        self.signals.messages.emit(QApplication.translate("DataWorker", "Reading file..."))
        if self.sampling == DataToolbar.RANDOM_ALL and self.lines_to_take is None:
            self.prep_sampling()
        path = str(self.filepath)
        data = []
        lines:list[int] = []
        lines_to_take = self.lines_to_take[:] if self.lines_to_take else None
        totallines = 0
        try:
            data, lines, totallines = self._read(path=path)
        except UnicodeDecodeError as u:
            self.signals.messages.emit(f"  Encoding error. Trying 'windows-1252'.")
            data, lines, totallines = self._read(path=path,  encoding="windows-1252")
        except Exception as e:
            print(traceback.format_exc())
            self.signals.messages.emit(f" Erroring opening {path}")
            self.signals.finished.emit((f"Error", e, None, None, None))
            return
        self.signals.messages.emit(f"  Opened {path}")
        results = (
            f"Took {len(data)} lines out of {totallines} seen",
            lines,
            path,
            data,
            lines_to_take,
            self.editable
        )
        self.signals.finished.emit(results)


    """
    def _all_headers(self, *, path:str, encoding:str="utf-8") -> list[str]:
        with DataFileReader( path, delimiter=self.delimiter, quotechar=self.quotechar, encoding=encoding ) as file:
            if not file.updates_headers:
                return None
            headers = []
            for i, line in enumerate( file.next() ):
                b = self.accept_line(i, line)
                if b is True:
                    for _ in file.current_headers:
                        if _ not in headers:
                            headers.append(_)
            headers.sort()
            return headers
    """

    def _read(self, *, path:str, encoding:str="utf-8") -> tuple[list,list]:
        t = 0
        i = 0
        lines:list[int] = []
        data:list[list[str]] = []
        #
        # jsonl may have all kinds of headers magic
        #
        #
        #_all_headers = self._all_headers(path=path, encoding=encoding)
        with DataFileReader( path, delimiter=self.delimiter, quotechar=self.quotechar, encoding=encoding ) as file:
            for line in file.next():
                b = self.accept_line(i, line)
                i += 1
                if b is True:
                    lines.append(i-1)
                    t += 1
                    data.append(line)
                elif b is None:
                    i = 0 if i <= 0 else i -1
                    break
        return (data, lines, i)

    def prep_sampling(self) -> None:
        needed = 0
        with DataFileReader( str(self.filepath) ) as file:
            for line in file.source:
                needed += 1
        #
        # find a random sample of lines within 0-i sufficient to fill up self.sample_size
        #
        # sample size can be < total lines. if so, we should reset the comboboxes to
        # reflect collecting all lines.
        #
        self.lines_to_take = []
        if self.sample_size >= needed -1:
            self.main.content.toolbar.rows.setCurrentIndex(4)
            self.sample_size = -1
            return
        to = min(needed-1, self.sample_size)
        for i in range(to):
            x = -1
            while x < 0:
                x = random.randint(0, needed)
                if x in self.lines_to_take:
                    x = -1
                else:
                    self.lines_to_take.append(x)
        self.lines_to_take.sort(reverse=True)

