from csvpath.matching.functions.function import Function
from csvpath.matching.functions.types.type import Type
from csvpath.matching.functions.function_focus import ValueProducer, MatchDecider

class FunctionParts:

    """
    function = {
        name,
        description,
        sigs[
            sig[
                arg{
                   "name":""
                    "types":[]
                    "actuals":[]
                }
            ]
        ]
        schema_type,
        focus,
        aliases[]
    }
    """


    @classmethod
    def describe(cls, function:Function) -> dict:
        cls.prep(function)
        desc = {}
        desc["name"] = function.name
        function.description = [] if function.description is None else function.description
        ds = []
        for s in function.description:
            ss = s.split("\n\n")
            for _ in ss:
                ds.append(_)
        desc["description"] = ds
        cls.aliases(function, desc)
        cls.sigs(function, desc)
        cls.schema_type(function, desc)
        cls.focus(function, desc)
        cls.qualifiers(function, desc)
        return desc

    @classmethod
    def aliases(cls, function:Function, desc:dict) -> None:
        desc["aliases"] = function.aliases

    @classmethod
    def qualifiers(cls, function:Function, desc:dict) -> None:
        desc["value_qualifiers"] = function.value_qualifiers if function.value_qualifiers else []
        desc["match_qualifiers"] = function.match_qualifiers if function.match_qualifiers else []
        desc["name_qualifier"] = function.name_qualifier if function.name_qualifier else ""

    @classmethod
    def prep(cls, function: Function) -> None:
        if not function.args:
            #
            # today this will most of the time blow up because we're
            # doing a structural validation of a function that is not
            # part of a structure. this should be refactored at some
            # point, but it's not hurting anything.
            #
            try:
                function.check_valid()
            except Exception:
                ...

    @classmethod
    def focus(cls, function:Function, desc:dict) -> None:
        stmts = []
        vp = isinstance(function, ValueProducer)
        md = isinstance(function, MatchDecider)
        if vp and md:
            desc["focus"] = "produces a calculated value and decides matches"
        elif vp:
            desc["focus"] = "produces a calculated value"
        elif md:
            desc["focus"] = "determines if lines match"
        else:
            desc["focus"] = "is a side-effect"

    @classmethod
    def schema_type(cls, function:Function, desc:dict) -> None:
        if isinstance(function, Type):
            desc["schema_type"] = "is a schema type"
        else:
            desc["schema_type"] = "is not a schema type"


    @classmethod
    def sigs(cls, function:Function, desc:dict) -> None:
        sigs = []
        desc["sigs"] = sigs
        args = function.args
        if not args:
            #
            # this is possibly due to the very small number of unrefactored functions. (3?)
            #
            return sigs
        argsets = args.argsets
        for ai, a in enumerate(argsets):
            a_sig = []
            sigs.append(a_sig)
            for i, _ in enumerate(a.args):
                an_arg = {}
                a_sig.append(an_arg)
                an_arg["name"] = _.name
                an_arg["actuals"] = []
                an_arg["types"] = []
                an_arg["noneable"] = _.is_noneable
                #
                # get types
                #
                for t in _.types:
                    t = cls._str_from_type(t)
                    an_arg["types"].append(t)
                for act in _.actuals:
                    act = cls._str_from_type(act)
                    an_arg["actuals"].append(str(act))
                if i == len(a.args)-1 and a.max_length == -1:
                    an_arg["unbounded"] = True
                else:
                    an_arg["unbounded"] = False

    @classmethod
    def _str_from_type(cls, t) -> str:
        if t is None:
            return ""
        t = str(t)
        if t.find("'") > -1 or t.find('"') > -1:
            i = t.find("'") if t.find("'") > -1 else t.find('"')
            t = t[i+1:]
            i = t.rfind("'") if t.rfind("'") > -1 else t.rfind('"')
            t = t[0:i]
        if str(t).find(".") > -1:
            t = str(t)[str(t).rfind(".")+1:]
        return t
