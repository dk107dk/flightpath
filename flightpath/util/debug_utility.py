from csvpath import CsvPaths

class DebugUtility:

    @classmethod
    def raise_csvpath_error(self) -> None:
        CsvPaths().collect_paths(filename="test",pathsname="fish")




