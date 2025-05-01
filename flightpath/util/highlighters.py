from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat
from PySide6.QtCore import Qt
from flightpath.util.span_utility import SpanUtility as sput

class MultiHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighters = []

    def highlightBlock(self, text):
        #print(f"""\t\t'''{text}''',""")
        for h in self.highlighters:
            h.highlightBlock(text)

class CommentHighlighter(QSyntaxHighlighter):
    def __init__(self, document=None, *, parent=None):
        super().__init__(document)
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(Qt.gray)
        self.parent = parent
        self.is_cont = sput.STOPPED
        self.formatted = []

    def highlightBlock(self, text):
        self.mark(text, "~")

    def is_cont(self) -> int:
        return self.previousBlockState()

    def is_cont(self, s:int) -> None:
        self.setCurrentBlockState(s)

    def mark(self, text, span_char):
        #
        # mark handles lines. spans chomps lines into ~ delimited chunks
        #
        spans = sput.find(text, "~")
        si = 0
        for s in spans:
            c = s[3][0]
            #
            # if we are active, but the first char make us inactive we need to flip
            #
            if c == "~" and self.is_cont:
                self.format(0, 1, [0,1, s[2], c])
                s[0] +=1
                s[1] -=1
                s[2] = False
                self.is_cont = sput.STOPPED
            #
            # do the fmat if we are continuing or have an active span
            #
            if self.is_cont == sput.CONTINUING or s[2] is True:
                self.format(s[0], s[1], s)

            c =  s[3][len(s[3])-1]
            #
            # c_bool determines if we will be continuing into the next span. True if:
            #  - doesn't start with "~"
            #  - starts with "~" but it is the first line so it's an opening
            #  - starts with "~" and the last line wasn't active, so it's an opening
            #
            c_bool = (c != "~") or (c == "~" and si == 0) or (c == "~" and spans[si-1][2] is False)
            if ( s[2] is True or self.is_cont == sput.CONTINUING ) and c_bool:
                self.is_cont = sput.CONTINUING
            else:
                self.is_cont = sput.STOPPED
            si += 1

    def format(self, from_char, len_chars, s) -> None:
        if self.parent:
            self.parent.setFormat(from_char, len_chars, self.comment_format)
        else:
            #
            # this option for testing
            #
            self.formatted.append(s)

