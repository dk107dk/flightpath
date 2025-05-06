import csv
import random

from PySide6.QtCore import Qt, QObject, Signal, Slot, QRunnable
from PySide6.QtWidgets import QApplication

from csvpath.util.file_readers import DataFileReader
from csvpath.matching.util.expression_utility import ExpressionUtility as exut

from flightpath.widgets.panels.data_viewer import DataViewer
from flightpath.widgets.panels.data_toolbar import DataToolbar

class DataWorkerSignals(QObject):
    finished = Signal(tuple)
    messages = Signal(str)

class GeneralDataWorker(QRunnable):

    def __init__(self, filepath, main, *, rows:str, sampling:str, delimiter=None, quotechar=None):
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

    def _rows(self, s) -> int:
        if s == "All lines":
            return -1
        i = exut.to_int(s)
        if not isinstance(i, int):
            i = 50
        return i

    def accept_line(self, line_num:int, line:list[str]) -> bool:
        #self.sample_size = self.sample_size if self.sample_size else -1
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
            #if line_num in self.lines_to_take:
                self.line_take += 1
                removed = self.lines_to_take.pop()
                return True
        return False

    @Slot()
    def run(self):
        self.signals.messages.emit(QApplication.translate("DataWorker", "Reading file..."))
        data = []
        if self.sampling == DataToolbar.RANDOM_ALL and self.lines_to_take is None:
            self.prep_sampling()
        path = str(self.filepath)
        lines:list[int] = []
        t = 0
        i = 0
        with DataFileReader( path ) as file:
            #
            # TODO: we don't need to handle CSV ourselves, right? shouldn't DataFileReader do it?
            #
            #
            # TODO: need to handle delimiters and quotechars
            #
            try:
                reader = csv.reader(file.source, delimiter=self.delimiter, quotechar=self.quotechar)
                max = self.sample_size
                for line in reader:
                    b = self.accept_line(i, line)
                    i += 1
                    if b is True:
                        lines.append(i-1)
                        t += 1
                        data.append(line)
                    elif b is None:
                        break
            except Exception as e:
                print(f"Error: {type(e)}: {e}")
        errors = []
        self.signals.messages.emit(QApplication.translate("DataWorker", f"  Opened {path}"))
        self.signals.finished.emit((f"Took {t} lines out of {i} seen", lines, path, data, errors))


    def prep_sampling(self) -> None:
        # find lines:
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
            self.main.content.data_view.toolbar.rows.setCurrentIndex(4)
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

