import os
import time
import darkdetect
from csvpath import CsvPath
from csvpath import CsvPaths
from csvpath.util.file_readers import DataFileReader
from csvpath.matching.functions.lines.dups import CountDups
class Inspector:

    def __init__(self, *, main, filepath:str) -> None:
        """
        print(f"\n\n\n")
        from csvpath.util.code import Code
        _ = Code.get_source_path(CountDups)
        print(f"{_}\n\n\n")
        """

        self.main = main
        self._filepath = filepath
        self._csvpath_str = None
        self._info = None
        self._path = None
        self._from_line = None
        self._sample_size = None
        self._headers = None
        self._config = None
        self._vars = None
        #
        # what is this about? we let the user choose cache or not. why override?
        #
        """
        if self.main:
            cwd = self.main.state.cwd
            cachedir = f"{cwd}{os.sep}cache"
            self.main.csvpath_config.set(section="cache", name="path", value=cachedir)
            self.main.csvpath_config.set(section="cache", name="use_cache", value="yes")
        """

    @property
    def vars(self) -> dict:
        return self._vars

    @vars.setter
    def vars(self, v:dict) -> None:
        self._vars = v

    @property
    def info(self) -> dict[str, str|int|float|bool|None]:
        if self._info is None:
            c = self.csvpath_str
            path = CsvPath()
            path.parse(c).fast_forward()
            self.vars = path.variables
            #
            # move the valuable info from vars to our own dict for jinja
            #
            self._info = self._populate(self.vars)
        return self._info


    def _populate(self, vs:dict) -> dict:

        info = {}
        info["ui_dark"] = darkdetect.isDark()
        info["file"] = self.filepath
        info["sample_size"] = self.sample_size
        info["from_line"] = self.from_line
        info["scan"] = self.compile_scan()
        info["header_count"] = self.header_count
        info["headers"] = self.headers
        info["total_lines"] = self.total_lines
        info["data_lines"] = self.data_lines
        info["blank_lines"] = self.blank_lines
        info["lines_with_blanks"] = self.lines_with_blanks
        info["duplicate_lines"] = self.duplicate_lines
        hd = {}
        info["header_details"] = hd
        for i, header in enumerate(self.headers):
            d = {}
            hd[header] = d
            d["name"] = header
            d["number"] = i
            d["duplicate_count"] = self.duplicate_count(i, header)
            d[f"types"] = self.header_types(i, header)
            d["is_distinct"] = self.is_distinct(i, header)
            d["min_val"] = self.min_val(i, header)
            d["max_val"] = self.max_val(i, header)
            d["is_not_none"] = self.is_not_none(i, header)
        return info

    @property
    def path(self) -> CsvPath:
        if self._path is None:
            self._path = CsvPath()
        return self._path

    @property
    def csvpath_str(self) -> str:
        if self._csvpath_str is None:
            self._csvpath_str = self.compile_csvpath(self.filepath)
        return self._csvpath_str

    @property
    def from_line(self) -> int:
        return self._from_line

    @from_line.setter
    def from_line(self, l:int) -> None:
        self._from_line = l

    @property
    def sample_size(self) -> int:
        return self._sample_size

    @sample_size.setter
    def sample_size(self, s:int) -> None:
        self._sample_size = s

    @property
    def filepath(self) -> str:
        return self._filepath

    @property
    def watermellon(self) -> list[str]:
        #
        # TODO: this is goofy, but I cannot see where I'm screwing up self.headers -- but apparently
        # somewhere, so for now watermellon. maybe the byte-order mark problem? seems unlikely.
        #
        if self._headers is None:
            self.path.get_total_lines_and_headers(filename=self.filepath)
            self._headers = self.path.headers
        return self._headers

    def compile_match(self) -> str:
        m = " not(all()) -> counter.lines_with_blanks() \n"
        m = f"{m} dup_lines() -> counter.total_duplicate_lines() \n"
        for i, header in enumerate(self.watermellon):
            #
            # this non-printing byteorder char seen in one of the example files
            # so far it only has shown here. we switched to numeric header refs
            # so it isn't a problem. leaving it as a reminder that that kind of
            # thing could happen elsewhere.
            #
            #header = header.replace('\ufeff', "")
            header = i
            m = f"""{m} \n\tpush.distinct("{header}_types", datatype(#{header}))"""
            m = f"""{m} \n\thas_dups(#{header}) -> counter.{header}_dups() """
            m = f"""{m} \n\tin(datatype(#{header}), "integer|decimal") -> @m = min.{header}_min(#{header}) """
            m = f"""{m} \n\tin(datatype(#{header}), "integer|decimal") -> @m = max.{header}_max(#{header}) \n"""
        return m

    def compile_scan(self) -> str:
        i = self.main.content.tab_widget.currentIndex()
        w = self.main.content.tab_widget.widget(i)
        c = w.table_view.model().rowCount()
        #
        # we won't sample more data than we have showing in the grid. trying to do that would
        # often put us outside the length of the data.
        #
        if self._sample_size > c:
            self._sample_size = c
        s = None
        if self._from_line:
            if self._from_line == 1 and self.filepath is not None:
                with DataFileReader(self.filepath) as file:
                    i = 0
                    self._from_line = 0
                    for line in file.source:
                        if i > 0 and line.strip() != "":
                            self._from_line = 1
                            break
                        i += 1
            s = self._from_line
        if self._sample_size:
            if s is None:
                s = f"0-{self._sample_size}"
            else:
                s = f"{self._from_line}-{self._from_line+self._sample_size}"
        else:
            if s is None:
                s = "*"
            else:
                s = f"{s}*"
        return s

    def compile_csvpath(self, filepath:str) -> str:
        match = self.compile_match()
        scan = self.compile_scan()
        pathstr = f"""
~
validation-mode:print, no-raise
~
${filepath}[{scan}][
{match}
]"""
        return pathstr

    @property
    def total_lines(self) -> int|None:
        return self.path.line_monitor._physical_end_line_count

    @property
    def data_lines(self) -> int|None:
        return self.path.line_monitor._data_end_line_count

    @property
    def blank_lines(self) -> int|None:
        return self.total_lines - self.data_lines

    @property
    def headers(self) -> list[str]:
        return self.path.headers

    @property
    def header_count(self) -> int:
        if self.path.headers:
            return len(self.path.headers)
        return 0

    @property
    def lines_with_blanks(self) -> int:
        return self.vars.get("lines_with_blanks")

    @property
    def duplicate_lines(self) -> int:
        return self.vars.get("total_duplicate_lines")


#-======================================
#
# "lines_with_blanks"
# not( all() ) -> counter.blank_headers()
#
# types
# multitype columns: push("types", )
#

#
# [ push.distinct("coltypes", type()) ]
#

    def duplicate_count(self, i:int, header:str) -> int:
        t = self.vars.get(f"{i}_dups")
        return t

    def header_types(self, i:int, header:str) -> list[str]:
        t = self.vars.get(f"{i}_types")
        t = str(t)
        t = t.replace("'", "")
        return t

    def is_distinct(self, i:int, header) -> int:
        t = f"{i}_dups"
        r = self.vars.get(t)
        return r is not None and r == 0


    def min_val(self, i:int, header) -> int|float:
        ts = self.header_types(i, header)
        if not ts:
            return ""
        if "decimal" in ts or "integer" in ts:
            i = self.vars.get(f"{i}_min")
            if not i:
                return ""
            if float(i) == int(i):
                return int(i)
            return float(i)
        return ""

    def max_val(self, i:int, header) -> int|float:
        _ = self.header_types(i, header)
        if not _:
            return ""
        if "decimal" in _ or "integer" in _:
            i = self.vars.get(f"{i}_max")
            if not i:
                return ""
            if float(i) == int(i):
                return int(i)
            return float(i)
        return ""

    def is_not_none(self, i:int, header) -> bool:
        t = self.vars.get(f"{i}_types")
        if t is None:
            return False
        return "none" not in t



