import os
import time
import darkdetect
from csvpath import CsvPath
from csvpath import CsvPaths

class Inspector:

    def __init__(self, *, main, filepath:str) -> None:
        self.main = main
        self._filepath = filepath
        self._csvpath_str = None
        self._info = None
        self._path = CsvPath()
        self._from_line = None
        self._sample_size = None
        self._headers = None
        self._config = None
        if self.main:
            cwd = self.main.state.cwd
            cachedir = f"{cwd}{os.sep}cache"
            self._path.config.set(section="cache", name="path", value=cachedir)
            self._path.config.set(section="cache", name="use_cache", value="yes")

    @property
    def info(self) -> dict[str, str|int|float|bool|None]:
        if self._info is None:
            c = self.csvpath_str
            self.path.parse(c).fast_forward()
            #
            # move the valuable info from vars to our own dict for jinja
            #
            self._info = self._populate(self.path.variables)
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
            d["unique_values"] = self.unique_values(i, header)
            d[f"types"] = self.header_types(i, header)
            d["is_distinct"] = self.is_distinct(i, header)
            d["min_val"] = self.min_val(i, header)
            d["max_val"] = self.max_val(i, header)
            d["is_not_none"] = self.is_not_none(i, header)
        return info

    @property
    def path(self) -> CsvPath:
        return self._path

    @property
    def variables(self) -> dict:
        return self.path.variables

    @property
    def csvpath_str(self) -> str:
        """
        from csvpath.util.log_utility import LogUtility as lout
        lout.log_brief_trace()
        """
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
            self._path.get_total_lines_and_headers(filename=self.filepath)
            self._headers = self._path.headers
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
            m = f"""{m} \n\tnot( has_dups(#{header}) ) -> counter.{header}_uniques() """
            m = f"""{m} \n\tin(datatype(#{header}), "integer|decimal") -> @m = min.{header}_min(#{header}) """
            m = f"""{m} \n\tin(datatype(#{header}), "integer|decimal") -> @m = max.{header}_max(#{header}) \n"""
        return m

    def compile_scan(self) -> str:
        s = None
        if self._from_line:
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
validation-mode:no-print, no-raise
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
        return self.path.variables.get("lines_with_blanks")

    @property
    def duplicate_lines(self) -> int:
        return self.path.variables.get("total_duplicate_lines")


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

    def unique_values(self, i:int, header:str) -> int:
        return self.path.variables.get(f"{i}_uniques")

    def header_types(self, i:int, header:str) -> list[str]:
        return self.path.variables.get(f"{i}_types")

    def is_distinct(self, i:int, header) -> int:
        if self.sample_size is None:
            return self.path.variables.get(f"{i}_uniques") == self.data_lines
        else:
            return self.path.variables.get(f"{i}_uniques") == self.sample_size

    def min_val(self, i:int, header) -> int|float:
        ts = self.header_types(i, header)
        if not ts:
            return ""
        if "decimal" in ts or "integer" in ts:
            i = self.path.variables.get(f"{i}_min")
            if not i:
                return ""
            if float(i) == int(i):
                return int(i)
            return float(i)
        return ""

    def max_val(self, i:int, header) -> int|float:
        if "decimal" in self.header_types(i, header) or "integer" in self.header_types(i, header):
            i = self.path.variables.get(f"{i}_max")
            if not i:
                return ""
            if float(i) == int(i):
                return int(i)
            return float(i)
        return ""

    def is_not_none(self, i:int, header) -> bool:
        t = self.path.variables.get(f"{i}_types")
        return "none" not in t



