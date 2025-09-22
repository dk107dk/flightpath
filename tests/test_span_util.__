import unittest

from flightpath.util.span_utility import SpanUtility as sput

class TestSpanUtility(unittest.TestCase):

    def test_in_comment_1(self):
        text = "~is a comment~"
        assert sput.in_comment(text, 3)
        assert not sput.in_comment(text, 0)
        assert not sput.in_comment(text, 14)

    def test_in_comment_2(self):
        text = """
        ---- CSVPATH ----
        ~ this is a comment ~
        $[*][ yes() ]
        """
        assert sput.in_comment(text, 40)
        assert not sput.in_comment(text, 70)

    def test_in_comment_3(self):
        print("")
        text = """
        ---- CSVPATH ----
        ~ this is a comment ~
        $[*][ ~me inside~ yes() ]
        """
        assert not sput.in_comment(text, 75)

    def test_in_comment_4(self):
        print("")
        text = """
        ---- CSVPATH ----
        ~ this is a comment ~
        $[*][ ~me inside~ yes() ]
        ---- CSVPATH ----
        ~ this is a comment ~
        $[*][ ~me inside~ yes() ]
        """
        print("\n== 1 ==")
        assert not sput.in_comment(text, 34)

        print("\n== 1.5 ==")
        assert sput.in_comment(text, 42)

        print("\n== 1.7 ==")
        assert not sput.in_comment(text, 75)

        print("\n== 2 ==")
        assert sput.in_comment(text, 127)

        print("\n== 3 ==")
        assert not sput.in_comment(text, 103)

        print("\n== 4 ==")
        assert sput.in_comment(text, 128)


