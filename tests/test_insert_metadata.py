import unittest
from flightpath.widgets.csvpath_text_edit import CsvPathTextEdit

class TestInsertMetadata(unittest.TestCase):

    ONE = " ~two fish~$[*][yes()]"

    TWO = """ ~ two fish ~ $[*][ yes()]"""

    THREE = """ ---- CSVPATH ---- ~ two fish ~ $[*][ yes()] """

    FOUR = """ $[*][ yes()] ---- CSVPATH ---- ~ two fish ~ $[*][ yes()] ---- CSVPATH ---- ~ three bugs ~ $[*][ yes() ] """



    def test_insert(self):
        print("")
        r,d = CsvPathTextEdit._add_to_external_comment_of_csvpath_at_position(
            text=TestInsertMetadata.ONE,
            position=20,
            addto="add me"
        )
        print(f"before:   {TestInsertMetadata.ONE}")
        print(f"after:    {r}")
        print(f"parts: {d}")
        assert r.strip() == "~add metwo fish~$[*][yes()]"

        print("")
        r,d = CsvPathTextEdit._add_to_external_comment_of_csvpath_at_position(
            text=TestInsertMetadata.TWO,
            position=20,
            addto="add me"
        )
        print(f"r: {r}")
        assert r.strip() == "~add me two fish ~ $[*][ yes()]"

        print("")
        r,d = CsvPathTextEdit._add_to_external_comment_of_csvpath_at_position(
            text=TestInsertMetadata.THREE,
            position=28,
            addto="add me"
        )
        print(f"r: {r}")
        assert r.strip() == """---- CSVPATH ---- ~add me two fish ~ $[*][ yes()]"""

        print("\n")
        r,d = CsvPathTextEdit._add_to_external_comment_of_csvpath_at_position(
            text=TestInsertMetadata.FOUR,
            position=50,
            addto="add me"
        )
        print(f"\nbefore:   {TestInsertMetadata.FOUR}")
        print(f"after:    {r}")
        print(f"parts: {d}")
        assert r.strip() == """$[*][ yes()] ---- CSVPATH ---- ~add me two fish ~ $[*][ yes()] ---- CSVPATH ---- ~ three bugs ~ $[*][ yes() ]"""





