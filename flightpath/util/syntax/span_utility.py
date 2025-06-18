
class SpanUtility:
    STOPPED = 0
    CONTINUING = 1

    @classmethod
    def find(cls, text, span_char) -> list[list]:
        spans = []
        while len(text) > 0:
            text = cls.chomp(spans, text, span_char)
            if text == "":
                break
            t = spans[len(spans)-1]
        return spans

    @classmethod
    def chomp(cls, spans, text, span_char) -> list[list]:
        a = -1
        active = None
        first = text[0] == span_char

        if first:
            a = text.find(span_char, 1)
            active = True
        else:
            a = text.find(span_char)
            active = False

        if a == -1:
            a = len(text)

        a = a+1 if first and len(text) > 1 else a
        take = text[0:a]
        ret = text[a:]
        spans.append( [0, a, active, take] )
        return ret


    @classmethod
    def in_comment(cls, text:str, pos:int) -> bool:
        #
        # TODO: make this method just returnthe set of booleans and another
        # that returns if in an external comment or not.
        #
        inc = False
        ins = False
        inroot = False
        inscan = False
        inmatch = False
        for i, c in enumerate(text):
            #print(c, end="")
            if i == pos:
                break
            if c == "$":
                ins = True
                inc = False
                inroot = True
                inscan = True
                inmatch = False
            elif c == "~":
                if inc:
                    inc = False
                elif ins:
                    inc = False
                else:
                    inc = True
            elif c == '[':
                if inroot:
                    inroot = False
                    inscan = True
                    inmatch = False
                    inc = False
                    ins = True
                elif inscan:
                    # error
                    ...
                else:
                    inmatch = True
            elif c == ']':
                if inmatch:
                    inmatch = False
                    ins = False
                    inc = False
                    inroot = False
                    inscan = False
                elif inscan:
                    inmatch = False
                    ins = True
                    inc = False
                    inroot = False
                    inscan = False
                else:
                    # error
                    ...
        """
        print(f"\n---------\nin root: {inroot}")
        print(f"in scan: {inscan}")
        print(f"in match: {inmatch}")
        print(f"in comment: {inc}")
        print(f"in statment: {ins}")
        """
        return inc

    @classmethod
    def insert(self, *, text, position, insert) -> str:
        return f"{text[:position]}{insert}{text[position:]}"


