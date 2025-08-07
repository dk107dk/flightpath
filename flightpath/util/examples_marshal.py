import os
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos
from flightpath.util.file_utility import FileUtility as fiut

class ExamplesMarshal:

    def __init__(self, main) -> None:
        self.main = main

    def add_examples(self, *, path:str, source_path=None) -> str:
        if source_path is None:
            source_path = fiut.make_app_path(os.path.join("assets", "examples"))
        #self.main.log(f"ExamplesMarshal: setting up examples from {source_path}")
        exampleslist = os.path.join(source_path, "list.txt")
        lst = None
        with DataFileReader(exampleslist) as file:
            lst = file.read()
        examples = lst.split("\n")
        #print(f"ExamplesMarshal: examples are {lst}")
        for example in examples:
            try:
                example = example.strip()
                if example == "":
                    continue
                if example.startswith("#"):
                    continue
                from_path = os.path.join(source_path, example)
                #print(f"ExamplesMarshal: from_path {from_path}")
                to_path = os.path.join(path,example)
                nos = Nos(os.path.dirname(to_path))
                if not nos.exists():
                    print(f"ExamplesMarshal: {to_path} dir {nos.path} does not exist. making it.")
                    nos.makedirs()
                with DataFileReader(from_path) as from_file:
                    with DataFileWriter(path=to_path) as to_file:
                        to_file.write(from_file.read())
            except Exception as e:
                from csvpath.util.log_utility import LogUtility as lout
                print(f"Error creating examples: {type(e)}: {e}")
                lout.log_brief_trace()
