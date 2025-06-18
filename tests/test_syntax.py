import unittest

from flightpath.util.syntax.span_utility import SpanUtility as sput
from flightpath.util.syntax.highlighters import CommentHighlighter

class TestSyntax(unittest.TestCase):

    def test_syntax_1(self):
        print("")
        text = "~is a comment~"
        spans = sput.find(text, "~", False)
        assert spans
        for i, s in enumerate(spans):
            print(f"{i}: {s}")
        assert len(spans) == 1
        assert spans[0] == (0, 14, True, "~is a comment~")


    def test_syntax_2(self):
        print("")
        text = "this ~is a comment~"
        spans = sput.find(text, "~", False)
        assert spans
        for i, s in enumerate(spans):
            print(f"{i}: {s}")
        assert len(spans) == 2
        assert spans[0] == (0, 5, False, "this ")

        assert spans[1] == (0, 14, True, "~is a comment~")


    def test_syntax_3(self):
        print("")
        text = "this ~is a comment~ yo"
        spans = sput.find(text, "~", False)
        assert spans
        for i, s in enumerate(spans):
            print(f"{i}: {s}")
        assert len(spans) == 3
        assert spans[0] == (0, 5, False, "this ")
        assert spans[1] == (0, 14, True, "~is a comment~")
        assert spans[2] == (0, 3, False, " yo")

    def test_syntax_4(self):
        print("")
        text = "this ~is a comment~ yo~~"
        spans = sput.find(text, "~", False)
        assert spans
        for i, s in enumerate(spans):
            print(f"{i}: {s}")
        assert len(spans) == 4
        assert spans[0] == (0, 5, False, "this ")
        assert spans[1] == (0, 14, True, "~is a comment~")
        assert spans[2] == (0, 3, False, " yo")
        assert spans[3] == (0, 2, True, "~~")

    def test_syntax_5(self):
        print("")
        text = "this ~is a comment~ yo~"
        spans = sput.find(text, "~", False)
        assert spans
        for i, s in enumerate(spans):
            print(f"{i}: {s}")
        assert len(spans) == 4
        assert spans[0] == (0, 5, False, "this ")
        assert spans[1] == (0, 14, True, "~is a comment~")
        assert spans[2] == (0, 3, False, " yo")
        assert spans[3] == (0, 1, True, "~")

## --------------------------------


    def test_formatter_1(self) -> None:
        print("")
        h = CommentHighlighter()
        blocks = [
            "~ id: test",
            "   validation-mode:print, collect, no-raise, no-stop",
            "        "   ,
            "   test-data: named_files/test.csv",
            "~ a"
        ]
        for b in blocks:
            h.highlightBlock(b)

        assert len(h.formatted) == 5
        assert h.formatted[0][3] == blocks[0]
        assert h.formatted[1][3] == blocks[1]
        assert h.formatted[2][3] == blocks[2]
        assert h.formatted[3][3] == blocks[3]
        assert h.formatted[4][3] == "~"

    def test_formatter_2(self) -> None:
        print("")
        h = CommentHighlighter()
        blocks = [
            "~ id: test",
            "   validation-mode:print, collect, no-raise, no-stop",
            "        "   ,
            "   test-data: named_files/test.csv",
            "~ ",
            " ",
            "$[*][",
            "	@random = subtract( line_number(), random(5,15) )",
            """	print("line $.csvpath.line_number is $.variables.random", "report")""",
            """ ~add("five", 3)~""",
            "]"
        ]
        for b in blocks:
            h.highlightBlock(b)

        for i, _ in enumerate(h.formatted):
            print(f"_[{i}]: {_}")

        assert len(h.formatted) == 6

        assert h.formatted[0][3] == blocks[0]
        assert h.formatted[1][3] == blocks[1]
        assert h.formatted[2][3] == blocks[2]
        assert h.formatted[3][3] == blocks[3]
        assert h.formatted[4][3] == "~"
        assert h.formatted[5][3] == blocks[9].strip()


    def test_formatter_3(self) -> None:
        print("")
        h = CommentHighlighter()
        blocks = [
            '''''',
            '''~''',
            '''   id: test''',
            '''   validation-mode:print, collect, no-raise, no-stop''',
            '''   ''',
            '''   test-data: named_files/test.csv''',
            '''~''',
            '''$[*][''',
            '''	@random = subtract( line_number(), random(5,15) )''',
            '''	print("line $.csvpath.line_number is $.variables.random", "report")''',
            '''	~add("five", 3)~''',
            ''']''',
            ''''''
        ]
        for b in blocks:
            h.highlightBlock(b)

        for i, _ in enumerate(h.formatted):
            print(f"_[{i}]: {_}")




