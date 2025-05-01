from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont
from PySide6.QtWidgets import QApplication, QPlainTextEdit
from PySide6.QtCore import Qt

class CsvpathHighlighter(QSyntaxHighlighter):
    def __init__(self, document=None, *, parent=None):
        if document is not None:
            super().__init__(document)
        self.highlighting_rules = []
        self.parent = parent

        try:
            keyword_format = QTextCharFormat()
            keyword_format.setForeground(Qt.darkBlue)
            keyword_format.setFontWeight(QFont.Bold)
            keywords = [
                "true()",
                "false()",
                "none()",
                "yes()",
                "no()",
                "notnone",
                "once",
                "onmatch",
                "nocontrib",
                "increase",
                "decrease",
                "latch",
                "strict",
                "mode",
                "distinct",
                "asbool",
                "->"

            ]
            keyword_pattern = r'\b(' + '|'.join(keywords) + r')\b'
            self.highlighting_rules.append((QRegularExpression(keyword_pattern), keyword_format))

            class_format = QTextCharFormat()
            class_format.setForeground(Qt.darkCyan)
            class_format.setFontWeight(QFont.Bold)
            self.highlighting_rules.append((QRegularExpression(r'\b[A-Z][a-zA-Z]*\b'), class_format))

            string_format = QTextCharFormat()
            string_format.setForeground(Qt.darkGreen)
            self.highlighting_rules.append((QRegularExpression(r'".*"'), string_format))

            """
            comment_format = QTextCharFormat()
            comment_format.setForeground(Qt.gray)
            self.highlighting_rules.append(
                QRegularExpression(r'~.*~', QRegularExpression.MultilineOption | QRegularExpression.DotMatchesEverythingOption),
                comment_format
            )
            """

            header_format = QTextCharFormat()
            header_format.setForeground(Qt.darkRed)
            self.highlighting_rules.append((QRegularExpression(r'#[^\.,-= ]*'), header_format))
        except Exception as e:
            print(f"rerror! {type(e)}: {e}")

    def highlightBlock(self, text):
        for regex, format in self.highlighting_rules:
            iterator = regex.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                start = match.capturedStart()
                length = match.capturedLength()
                if self.parent:
                    self.parent.setFormat(start, length, format)
                else:
                    self.setFormat(start, length, format)


