import os
from csvpath.util.path_util import PathUtility as pathu
from flightpath.util.file_utility import FileUtility as fiut

class HelpFinder:

    def __init__(self, main) -> None:
        self.main = main

    def help(self, path:str, fallback=None) -> str:
        mdpath = fiut.make_app_path(f"assets{os.sep}help{os.sep}{path}")
        mdpath = pathu.resep(mdpath)
        md = ""
        if os.path.exists(mdpath):
            with open(mdpath, "r", encoding="utf-8") as file:
                md = file.read()
                if md:
                    md = md.replace("{mydir}", os.path.dirname(mdpath))
                    md = md.replace("{sep}", os.sep)
            return md
        elif fallback is not None:
            self.help(fallback)

