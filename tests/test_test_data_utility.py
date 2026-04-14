import unittest
from flightpath.util.tdata_utility import TDataUtility as tdut


class TestTestDataUtil(unittest.TestCase):
    def test_get_test_data_path(self):
        text = """
            ~ test-data:a/b/c.csv ~
            $[*][ yes()]
        """
        path = tdut.test_data_path_from_csvpath(text)
        print(f"path: {path}")
        assert path == "a/b/c.csv"
