import unittest
from flightpath.util.test_data_utility import TestDataUtility as tdut

class TestTestDataUtil(unittest.TestCase):

    def test_get_test_data_path(self):
        text = """
            ~ test-data:a/b/c.csv
            $[*][ yes()]
        """
        path = tdut.test_data_path_from_csvpath(text)
        print(f"path: {path}")
        assert path == "a/b/c.csv"


