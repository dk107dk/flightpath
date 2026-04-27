from csvpath.util.metadata_parser import MetadataParser
from csvpath.managers.paths.paths_manager import PathsManager
from csvpath.matching.util.expression_utility import ExpressionUtility as exut


class CsvpathUtility:
    CHAR_NAMES = {
        "pipe": "|",
        "bar": "|",
        "semi-colon": ";",
        "semicolon": ";",
        "comma": ",",
        "colon": ":",
        "hash": "#",
        "percent": "%",
        "star": "*",
        "asterisk": "*",
        "at": "@",
        "~": "tilde",
        "int": None,
        "quotes": '"',
        "quote": '"',
        "single-quotes": "'",
        "singlequotes": "'",
        "singlequote": "'",
        "single-quote": "'",
        "tick": "`",
        "tab": None,
    }

    @classmethod
    def statement_and_comment(cls, csvpath: str) -> tuple[str, str]:
        mdatap = MetadataParser(None)
        cstr, comment = mdatap.extract_csvpath_and_comment(csvpath)
        cstr = cstr.strip()
        comment = comment.strip()
        return cstr, comment

    @classmethod
    def get_metadata(cls, comment: str) -> None:
        mdata = {}
        MetadataParser(None)._collect_metadata(mdata, comment)
        return mdata

    @classmethod
    def get_filepath(cls, comment: str) -> str:
        comment = "" if comment is None else comment.strip()
        mdata = {}
        if len(comment) > 0:
            mdata = cls.get_metadata(comment)
        #
        # should we pathu.resep to make sure we're converting to \ if needed?
        # has not shown up as a problem on Windows yet, tho.
        #
        filepath = mdata.get("test-data")
        if filepath is None:
            return None
        filepath = filepath.strip()
        filepath = (
            filepath if filepath.find("\n") == -1 else filepath[0 : filepath.find("\n")]
        )
        if not filepath.startswith("/"):
            #
            # check if we lopped off a leading '/'. metadata parser has a bug.
            # this is a stupid hack.  :/
            #
            i = comment.find(filepath)
            if i > 0 and comment[i - 1] == "/":
                return f"/{filepath}"
        return filepath

    @classmethod
    def get_delimiter(cls, comment: str = None) -> str:
        c = None
        mdata = cls.get_metadata(comment)
        if mdata:
            c = mdata.get("test-delimiter")
            if c:
                c = cls._get_char(c, ",")
        return c

    @classmethod
    def get_quotechar(cls, comment: str = None) -> str:
        c = None
        mdata = cls.get_metadata(comment)
        if mdata:
            c = mdata.get("test-quotechar")
            if c:
                c = cls._get_char(c, '"')
        return c

    @classmethod
    def _get_char(cls, c: str, default: str) -> str:
        #
        # CsvPath does not support special characters in metadata. they are
        # allowed, but not preserved. that means we cannot assume test-delimiter
        # will just hold the actual delimiter char. we need to parse a char
        # name and use that to find the right delimiter char.
        #
        # we could do this a few ways. one approach would be to use the HTML
        # char codes (e.g. &nbsp;) but that feels hard for everyone. better to
        # just use "bar", "pipe", "semi-colon", "quotes", etc.
        #
        if c == "int":
            try:
                c = chr(exut.to_int(c))
            except Exception:
                ...
        elif c == "tab":
            c = "\t"
        else:
            try:
                c = cls.CHAR_NAMES.get(c)
            except Exception:
                ...
        if c is None:
            c = default
        c = c.strip()
        return c

    @classmethod
    def _add_to_external_comment_of_csvpath_at_position(
        cls, *, text: str, position: int, addto: str
    ) -> tuple[str, dict]:
        #
        # text: the whole file
        # position: where the cursor is, indicating which csvpath
        # addto: information we want to add to the external comment
        #
        # the addto string will go into the external comment above the
        # csvpath the position is in. adding addto to a trailing
        # csvpath comment is untested and may not work.
        #
        # we return the new string and a dict of the parts of the original string + the
        # additional metadata. the latter is only for debugging. it could go away, but
        # it does no harm to leave it while the code is new and the unit tests small.
        #
        if position >= len(text):
            raise ValueError(f"Index {position} out of string: {text}")
        #
        #                                                 V
        # $[*][ yes()] ---- CSVPATH ---- ~ two fish ~ $[*][ yes()] ---- CSVPATH ---- ~ three bugs ~ $[*][ yes() ]
        # |--------------------top-------------------------|----------bottom------------------------------------|
        # |--------------over-----------|------head--------|-tail--|---------under------------------------------|
        #                              |s|--comment-|-pre-|
        #                                /\
        #                               /m\
        #
        #
        top = None
        bottom = None
        over = None
        head = None
        tail = None
        under = None
        s = None
        comment = None
        pre = None
        #
        # find major parts
        #
        top = text[0:position]
        bottom = text[position:]
        _ = top.rfind(PathsManager.MARKER)
        if _ == -1:
            over = ""
            head = top
        else:
            over = top[0:_]
            head = top[_:]
        _ = bottom.find(PathsManager.MARKER)
        if _ == -1:
            tail = bottom
            under = ""
        else:
            tail = bottom[0:_]
            under = bottom[_:]
        #
        # parse head further
        #
        if head.find("~") > -1:
            _ = head.find("~")
            s = head[0 : _ + 1]
            comment = head[_ + 1 : head.rfind("~") + 1]
            pre = head[head.rfind("~") + 1 :]
        else:
            s = "~"
            comment = "~"
            pre = head
        #
        # build the new string and collect the dict for checking, if needed.
        #
        return (
            f"{over}{s}{addto}{comment}{pre}{tail}{under}",
            {
                "over": over,
                "s": s,
                "addto": addto,
                "comment": comment,
                "pre": pre,
                "tail": tail,
                "under": under,
            },
        )
