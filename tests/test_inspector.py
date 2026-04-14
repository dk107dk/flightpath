import unittest
import os
from flightpath.inspect.inspector import Inspector
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.html_generator import HtmlGenerator


class TestInspector(unittest.TestCase):
    def test_inspect_file(self):
        path = "tests/test_resources/examples/test.csv"
        inspector = Inspector(main=None, filepath=path)
        inspector.sample_size = 25
        inspector.from_line = 1
        t = fiut.make_app_path(
            f"assets{os.sep}help{os.sep}templates{os.sep}file_details.html"
        )
        html = HtmlGenerator.load_and_transform(t, inspector.info)
        assert html is not None and len(html.strip()) > 0
        with open("test.html", "w") as file:
            file.write(html)

    def test_compile_scan(self):
        path = "tests/test_resources/examples/test.csv"
        inspector = Inspector(main=None, filepath=path)
        inspector.sample_size = 50
        scan = inspector._compile_scan(c=5000)
        assert scan == "0-50"
        scan = inspector._compile_scan(c=5)
        assert scan == "0-5"
