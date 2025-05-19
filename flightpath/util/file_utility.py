import os

from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader
from csvpath.util.path_util import PathUtility as pathu

class FileUtility:
    APP_PATH = None

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
        """
        if not os.path.exists(path):
            #
            # log files can not exist if we've never used it.
            #
            return
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        n = cls.count_files(dirpath)
        n += 1
        t = os.path.join(dirpath, f"{os.path.basename(path)}_{n}")
        os.rename(path, t)
        """

    @classmethod
    def count_files(cls, dirpath:str) -> int:
        nos = Nos(dirpath)
        lst = nos.listdir()
        return len(lst)
        """
        i = 0
        for i, f in enumerate( os.listdir(dirpath) ):
            ...
        return i
        """

    @classmethod
    def is_in(path:str, is_in_dir:str) -> bool:
        return os.path.dirname(path) == os.path.basename(is_in_dir)
