import unittest
import os

from csvpath.util.nos import Nos

from flightpath.util.string_utility import StringUtility as strut

class TestStringUtil(unittest.TestCase):

    def test_to_list(self):
        text = """
            { "a":"b"}{
            "c":
            "d"
            }
        """
        lst = strut.jsonl_text_to_list(text)
        print(f"lst: {lst}")
        assert lst
        assert len(lst) == 2


