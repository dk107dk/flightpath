from csvpath.util.printer import Printer

class CapturePrinter(Printer):
    def __init__(self):
        self._last_line = None
        self._count = 0
        self._printouts = {}

    @property
    def names(self) -> list[str]:
        names = list(self._printouts.keys())
        if Printer.DEFAULT not in names:
            names.append(Printer.DEFAULT)
        return names

    def printouts(self, name:str) -> list[str]:
        lines = self._printouts.get(name)
        if name == Printer.DEFAULT and lines is None:
            lines = []
        return lines

    @property
    def lines_printed(self) -> int:
        return self._count

    def to_string(self, name:str) -> str:
        lst = self._printouts.get(name)
        if lst is None:
            return ""
        return "\n".join(lst)

    @property
    def last_line(self) -> str:
        return self._last_line

    def print(self, string: str) -> None:
        self.print_to(Printer.DEFAULT, string)

    def print_to(self, name: str, string: str) -> None:
        self._count += 1
        lines = self._printouts.get(name)
        if lines is None:
            lines = []
            self._printouts[name] = lines
        lines.append(string)
        self._last_line = string



