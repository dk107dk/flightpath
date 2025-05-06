import unittest
import os

from flightpath.util.examples_marshal import ExamplesMarshal
from csvpath.util.nos import Nos

class TestExamples(unittest.TestCase):

    def test_examples_1(self):
        print("")
        source = f"tests{os.sep}test_resources{os.sep}examples_source"
        examples = f"tests{os.sep}test_resources{os.sep}examples"

        nos = Nos(source)
        assert nos.exists()

        nos = Nos(examples)
        if nos.exists():
            nos.remove()
        if not nos.exists():
            nos.makedirs()

        assert len(nos.listdir()) == 0
        #
        # ready to create examples
        #
        em = ExamplesMarshal(None)
        em.add_examples(path=examples, source_path=source)
        #
        # nos should find the dir and two example files
        #
        nos = Nos(examples)
        assert nos.exists()
        assert len( nos.listdir() ) == 2
