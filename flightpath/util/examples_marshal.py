import os
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos
#from csvpath.util.path_util import PathUtility as pathu
from flightpath.util.file_utility import FileUtility as fiut

class ExamplesMarshal:

    def __init__(self, main=None) -> None:
        self.main = main

    def add_examples(self, *, path:str, source_path=None) -> str:
        if source_path is None:
            source_path = fiut.make_app_path(os.path.join("assets", "examples"))
        exampleslist = os.path.join(source_path, "list.txt")
        lst = None
        with DataFileReader(exampleslist) as file:
            lst = file.read()
        examples = lst.split("\n")
        for example in examples:
            try:
                example = example.strip()
                if example == "":
                    continue
                if example.startswith("#"):
                    continue
                from_path = os.path.join(source_path, example)
                to_path = os.path.join(path,example)
                nos = Nos(os.path.dirname(to_path))
                if not nos.exists():
                    nos.makedirs()
                with DataFileReader(from_path) as from_file:
                    with DataFileWriter(path=to_path) as to_file:
                        to_file.write(from_file.read())
            except Exception as e:
                print(f"Error creating examples: {type(e)}: {e}")

