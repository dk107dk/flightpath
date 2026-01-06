import re
from PySide6 import QtCore, QtGui
import darkdetect
from flightpath.widgets.editor.lexer import TokenID, Token, Lexer
from flightpath.util.syntax.csvpath_highlighter import CsvPathSyntaxHighlighter

class JsonHighlighter (QtGui.QSyntaxHighlighter):
    """Syntax highlighter for the JSON format.
    """

    def __init__(self, parent: QtGui.QTextDocument) -> None:
        super().__init__(parent)

        self.mappings = {}
        self.standard = CsvPathSyntaxHighlighter()
        self.colors = None
        self.set_colors()
        #self.colors = self.standard.dark_colors if darkdetect.isDark() else self.standard.colors
        #self.setup_highlight()

    def set_colors(self) -> None:
        colors = self.standard.dark_colors if darkdetect.isDark() else self.standard.colors
        if colors != self.colors:
            self.colors = colors
            self.setup_highlight()

    def setup_highlight(self):
        key_format = QtGui.QTextCharFormat()
        c = self.colors["string"]
        key_format.setForeground(c)
        #key_format.setForeground(QtCore.Qt.blue)
        self.mappings[TokenID.KEY] = key_format

        string_format = QtGui.QTextCharFormat()
        c = self.colors["string"]
        string_format.setForeground(c)
        #string_format.setForeground(QtCore.Qt.GlobalColor.darkGreen)
        self.mappings[TokenID.STRING] = string_format

        int_format = QtGui.QTextCharFormat()
        c = self.colors["number"]
        int_format.setForeground(c)
        #int_format.setForeground(QtCore.Qt.GlobalColor.cyan)
        self.mappings[TokenID.INT] = int_format

        null_format = QtGui.QTextCharFormat()
        c = self.colors["none"]
        null_format.setForeground(c)
        #null_format.setForeground(QtCore.Qt.GlobalColor.red)
        self.mappings[TokenID.NULL] = null_format

        bool_format = QtGui.QTextCharFormat()
        c = self.colors["bool"]
        key_format.setForeground(c)
        #bool_format.setForeground(QtCore.Qt.GlobalColor.magenta)
        self.mappings[TokenID.BOOL] = bool_format

        separator_format = QtGui.QTextCharFormat()
        separator_format.setFontWeight(QtGui.QFont.Bold)
        separator_format.setForeground(QtCore.Qt.GlobalColor.lightGray)
        self.mappings[TokenID.COLON] = separator_format
        self.mappings[TokenID.COMMA] = separator_format
        self.mappings[TokenID.LEFT_SQ_BRACKET] = separator_format
        self.mappings[TokenID.RIGHT_SQ_BRACKET] = separator_format
        self.mappings[TokenID.LEFT_CURL_BRACKET] = separator_format
        self.mappings[TokenID.RIGHT_CURL_BRACKET] = separator_format

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """
        lexer = Lexer(text)
        for token_id, start, end in lexer.lex():
            fmt = self.mappings.get(token_id)
            if fmt is None:
                continue
            self.setFormat(start, end - start, fmt)

