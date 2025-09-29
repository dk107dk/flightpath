import os
from pathlib import Path

from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.path_util import PathUtility as pathu
from .os_utility import OsUtility as osut

class FileUtility:
    APP_PATH = None

    @classmethod
    def copy_results_back_to_cwd(self, *, main, from_path:str) -> str:
        to_index = main.sidebar.file_navigator.currentIndex()
        to_path = None
        if to_index.isValid():
            to_path = main.sidebar.proxy_model.filePath(to_index)
        else:
            to_path = main.state.cwd
        to_nos = Nos(to_path)
        if to_nos.isfile():
            to_path = os.path.dirname(to_path)
        to_path = FileUtility.deconflicted_path(to_path, f"{os.path.basename(from_path)}")
        to_nos.path = to_path
        with DataFileReader(from_path) as ffrom:
            with DataFileWriter(path=to_path) as tto:
                tto.write(ffrom.read())
        return to_path

    @classmethod
    def read_string(cls, path) -> str:
        with DataFileReader(path) as reader:
            return reader.read()


    @classmethod
    def deconflicted_path(cls, path, name) -> str:
        apath = os.path.join(path, name)
        name = cls.deconflict_file_name(apath)
        return os.path.join(path, name)

    @classmethod
    def deconflict_file_name(cls, path) -> str:
        directory = os.path.dirname(path)
        name = os.path.basename(path)
        nos = Nos(path)
        i = 0
        ss = cls.split_filename(name)

        if ss[1].strip() == '':
            ...
        else:
            ss[1] = f".{ss[1]}"
        while nos.exists():
            name = f"{ss[0]}({i}){ss[1]}"
            _ = os.path.join(directory, name)
            nos.path = _
            i += 1
        return name

    @classmethod
    def split_filename(cls, name) -> tuple[str, str]:
        name = os.path.basename(name)
        e = name.find(".")
        if e == -1:
            return [name, '']
        return [name[0:e], name[e+1:]]

    @classmethod
    def make_app_path(cls, path, *, main=None) -> str:
        ap = cls.app_path()
        t = os.path.join(ap, "flightpath")
        t1 = os.path.join( t, path)
        t2 = None
        if Nos(t1).exists():
            return t1
        t2 = os.path.join( ap, path)
        if Nos(t2).exists():
            return t2
        if main:
            main.log(f"Fiut: cannot find {path} at {t1} or {t2}")
        else:
            print(f"Fiut: cannot find {path} at {t1} or {t2}")
        return None

    @classmethod
    def app_path(cls) -> str:
        if cls.APP_PATH is None:
            # up to util
            path = os.path.dirname(__file__)
            # up to flightpath
            path = os.path.dirname(path)
            # this is the home of the exe
            cls.APP_PATH = os.path.dirname(path)
        return cls.APP_PATH

    @classmethod
    def move_file_to_numbered(cls, path:str, dirpath:str=".") -> None:
        nos = Nos(path)
        if not nos.exists():
            return
        nos.path = dirpath
        if not nos.exists():
            nos.makedirs()
        n = cls.count_files(dirpath)
        n += 1
        t = os.path.join(dirpath, f"{os.path.basename(path)}_{n}")
        nos = Nos(path)
        t = pathu.resep(t)
        nos.rename(t)

    @classmethod
    def count_files(cls, dirpath:str) -> int:
        nos = Nos(dirpath)
        lst = nos.listdir()
        return len(lst)

    @classmethod
    def is_in(path:str, is_in_dir:str) -> bool:
        return os.path.dirname(path) == os.path.basename(is_in_dir)

    @classmethod
    def real_home_dir(self) -> str:
        """ this method gets the expected home dir for macos regardless of sandboxing
            that may not be what you want because it may not be writable """
        home = str(Path.home())
        if osut.is_mac():
            if home.find("Container") > -1:
                parts = pathu.parts(home)
                print(f"fiut: real_home_dir: {parts}")
                home = f"/{parts[1]}/{parts[2]}"
        return home

    @classmethod
    def is_new_writable(cls, path) -> bool:
        try:
            if os.path.exists(path):
                #
                # the name must be available
                #
                return False
            if not os.path.exists(os.path.dirname(path)):
                return False
            with open( path, "w" ) as file:
                file.write("test")
            nos = Nos(path)
            if nos.exists():
                print("main.is_new_writable: file exists")
                nos.remove()
                return True
            else:
                print("main.is_new_writable: not writable")
                return False
        except Exception as e:
            print(f"Error in is_new_writable: {type(e)}: {e}")
            return False

    @classmethod
    def is_writable_dir(cls, path) -> bool:
        print(f"main.is_writable_dir: checking writeability of: {path}")
        try:
            if not os.path.exists(path):
                return False
            from uuid import uuid4
            t = f"{uuid4()}"
            p = os.path.join(path, t)
            print(f"main.is_writable_dir: attempting to write to: {p}")
            return cls.is_new_writable(p)
        except Exception as e:
            print(f"Error in is_writable_dir: {type(e)}: {e}")
            return False

    @classmethod
    def to_sandbox_path(cls, path:str) -> str:
        if osut.is_mac() and osut.is_sandboxed():
            insert = "/Library/Containers/com.flightpathdata.flightpath"
            # do stuff
            if path.find(insert) > -1:
                print(f"FileUtility.to_sandbox_path: {path} appears to be in sandbox already.")
                return path
            #
            # separating out Data is probably not needed, but it doesn't hurt and may help in some cases
            #
            insert = os.path.join(insert, "Data")
            if path.startswith( os.path.expanduser('~') ):
                print(f"FileUtility.to_sandbox_path: {path} is under the user's home at {os.path.expanduser('~')}")
                top = path[0:len(os.path.expanduser('~'))]
                bottom = path[len(os.path.expanduser('~')):]
                new_path = f"{top}{insert}{bottom}"
            elif path.startswith("/Users/"):
                print(f"FileUtility.to_sandbox_path: {path} is under the users home at /Users/")
                parts = pathu.parts(path)
                bottom = path[len(f"/Users/{parts[2]}"):]
                new_path = f"/Users/{parts[2]}{insert}{bottom}"
            print(f"FileUtility.to_sandbox_path: {path} converted to {new_path}")
            #
            # not checking for existance or writability. caller's responsibility.
            #
            ndir = new_path
            if os.path.exists(ndir) and os.path.isfile(ndir):
                ndir = os.path.dirname(ndir)
            if not cls.is_writable_dir(ndir):
                print(f"FileUtility.to_sandbox_path: converted dir {ndir} is not writable")
                return None
            return new_path
        elif osut.is_sandboxed():
            print(f"Error: FileUtility.to_sandbox_path: must be a mac if sandboxed")
            return None
        else:
            print(f"FileUtility.to_sandbox_path: not a mac. Cannot try to convert {path} to sandbox path.")
            return None
