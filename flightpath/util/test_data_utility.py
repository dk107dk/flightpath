
from csvpath.util.metadata_parser import MetadataParser
from csvpath.util.file_readers import DataFileReader
from csvpath.managers.paths.paths_manager import PathsManager


class TestDataUtility:
    MARKER:str = PathsManager.MARKER

    @classmethod
    def get_test_data_path(cls, path:str) -> str:
        print(f"TestDataUtility: get_test_data_path: path: {path}")
        csvpath = None
        with DataFileReader(path) as file:
            csvpath = file.read()
        return cls.test_data_path_from_csvpath(csvpath)

    @classmethod
    def test_data_path_from_csvpath(cls, csvpath:str) -> str:
        stmt = None
        c = None
        for _ in csvpath.split(TestDataUtility.MARKER):
            if _.find("test-data:") > -1:
                stmt, c = cls.statement_and_comment(_)
                break
        print(f"ask: _get_data_path: stmt: {stmt}")
        if stmt is None:
            return None
        ret = cls.get_filepath(stmt, c)
        return ret

    @classmethod
    def statement_and_comment(cls, csvpath:str) -> tuple[str,str]:
        mdatap = MetadataParser(None)
        cstr, comment = mdatap.extract_csvpath_and_comment(csvpath)
        cstr = cstr.strip()
        comment = comment.strip()
        return cstr, comment

    @classmethod
    def get_filepath(cls, cstr:str, comment:str) -> str:
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
        filepath = filepath if filepath.find("\n") == -1 else filepath[0:filepath.find("\n")]
        if not filepath.startswith("/"):
            #
            # check if we lopped off a leading '/'. metadata parser has a bug.
            # this is a stupid hack.  :/
            #
            i = comment.find(filepath)
            if i > 0 and comment[i-1] == '/':
                return f"/{filepath}"
        return filepath

    @classmethod
    def get_metadata(cls, comment:str) -> None:
        mdatap = MetadataParser(None)
        mdata = {}
        mdatap._collect_metadata(mdata, comment)
        return mdata

