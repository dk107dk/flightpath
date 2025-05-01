
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





