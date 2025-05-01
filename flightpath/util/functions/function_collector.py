
from csvpath.matching.functions.function_factory import FunctionFactory
from csvpath.matching.functions.function import Function

class FunctionCollector:

    def __init__(self) -> None:
        self._functions = None

    @property
    def functions(self) -> dict[str,dict[str,Function]]:
        if self._functions is None:
            FunctionFactory.load()
            names = list(FunctionFactory.MY_FUNCTIONS.keys())
            functs = {}
            for name in names:
                #
                # get each function. find it's bucket (directory where the class lives)
                #
                f = FunctionFactory.get_function(None, name=name, child=None, find_external_functions=False)
                cname = str(type(f))
                mname = f.__module__
                #
                # looks like:
                # <class 'csvpath.matching.functions.boolean.between.Between'>
                #
                bucketname:str = mname[0: mname.rfind(".")]
                bucketname = bucketname[bucketname.rfind(".")+1:]
                bucket:dict = functs.get(bucketname)
                if bucket is None:
                    bucket = {}
                    functs[bucketname] = bucket
                bucket[name] = f
            self._functions = functs
        return self._functions

    def _name_for_type_str(self, t:str) -> str:
        t = t[t.find("'") + 1:]
        t = t[0:t.rfind("'")]

    @property
    def function_names(self) -> dict[str, list[str]]:
        fns = {}
        functions = self.functions
        for k, v in functions.items():
            names = list(v.keys())
            names.sort()
            fns[k] = names
        return fns




