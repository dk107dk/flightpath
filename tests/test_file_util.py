import unittest
import os

from csvpath.util.nos import Nos

from flightpath.util.file_utility import FileUtility as fiut

class TestFiut(unittest.TestCase):

    def test_deconflict_name_1(self):
        aname = "test.txt"
        apath = "tests/test_resources/deconflict"
        nos = Nos(apath)
        names = nos.listdir()
        for name in names:
            if name == aname:
                continue
            nos.path = os.path.join(apath, name)
            nos.remove()
        apath = fiut.deconflicted_path(apath, aname)
        assert apath == "tests/test_resources/deconflict/test(0).txt"


    def test_deconflict_name_2(self):
        path = "tests/test_resources/deconflict/test.txt"
        #
        # clear dir
        #
        dirname = os.path.dirname(path)
        nos = Nos(os.path.dirname(path))
        names = nos.listdir()
        for name in names:
            if name == "test.txt":
                continue
            nos.path = os.path.join(dirname, name)
            nos.remove()
        #
        # 1 conflict
        #
        name = fiut.deconflict_file_name(path)
        print(f"name: {name}")
        assert name
        assert name == "test(0).txt"
        np = os.path.join(dirname, name)
        assert not Nos(np).exists()
        with open(np, mode="w") as file:
            file.write("")

        name = fiut.deconflict_file_name(path)
        np = os.path.join(dirname, name)
        print(f"name: {name}")
        assert name
        assert name == "test(1).txt"
        assert not Nos(np).exists()
        with open(np, mode="w") as file:
            file.write("")


