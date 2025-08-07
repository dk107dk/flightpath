import re
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter
from PySide6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget
import darkdetect
#
# this class is all claude. take this comment out if/when we work on it.
#
class CsvPathSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Define highlighting rules as (pattern, format) tuples
        self.highlighting_rules = []

        # Define text formats for different syntax elements
        self._formats = {
            'comment': self._create_format(QColor(128, 128, 128), italic=True),
            'string': self._create_format(QColor(163, 21, 21)),
            'regex': self._create_format(QColor(196, 26, 22)),
            'header': self._create_format(QColor(25, 23, 124), bold=True),
            'variable': self._create_format(QColor(9, 134, 88), bold=True),
            'reference': self._create_format(QColor(136, 19, 145), bold=True),
            'function': self._create_format(QColor(0, 0, 255)),
            'number': self._create_format(QColor(0, 153, 153)),
            'operator': self._create_format(QColor(255, 0, 0), bold=True),
            'bracket': self._create_format(QColor(0, 0, 0), bold=True),
            'punctuation': self._create_format(QColor(0, 0, 0))
        }

        # Define text formats for different syntax elements
        self._formats_dark = {
            'comment': self._create_format(QColor(128, 128, 128), italic=True),
            'string': self._create_format(QColor(163, 121, 121)),
            'regex': self._create_format(QColor(196, 126, 122)),
            'header': self._create_format(QColor(125, 183, 124), bold=True),
            'variable': self._create_format(QColor(9, 134, 88), bold=True),
            'reference': self._create_format(QColor(136, 119, 145), bold=True),
            'function': self._create_format(QColor(100, 200, 255)),
            'number': self._create_format(QColor(0, 153, 153)),
            'operator': self._create_format(QColor(255, 100, 80), bold=True),
            'bracket': self._create_format(QColor(110, 110, 110), bold=True),
            'punctuation': self._create_format(QColor(220, 220, 220))
        }



        # Build highlighting rules based on the grammar
        self._build_rules()

    def _create_format(self, color, bold=False, italic=False):
        """Helper to create a QTextCharFormat with given properties"""
        format = QTextCharFormat()
        format.setForeground(color)
        if bold:
            format.setFontWeight(QFont.Bold)
        if italic:
            format.setFontItalic(True)
        return format

    @property
    def formats(self) -> dict:
        if darkdetect.isDark():
            return self._formats_dark
        return self._formats

    def _build_rules(self):
        """Build the highlighting rules based on CsvPath grammar"""

        # Comments: ~...~
        self.highlighting_rules.append((
            re.compile(r'~[^~]*~'),
            self.formats['comment']
        ))

        # Strings: "..."
        self.highlighting_rules.append((
            re.compile(r'"[^"]*"'),
            self.formats['string']
        ))

        # Regular expressions: /.../ (but not division operators)
        # Look for / followed by regex content and closing /
        self.highlighting_rules.append((
            re.compile(r'/([^/\\]|\\.)*?/'),
            self.formats['regex']
        ))

        # Headers: #identifier or #"quoted identifier"
        self.highlighting_rules.append((
            re.compile(r'#"[a-zA-Z0-9 \._]+"'),
            self.formats['header']
        ))
        self.highlighting_rules.append((
            re.compile(r'#[a-zA-Z0-9\._]+'),
            self.formats['header']
        ))

        # Variables: @identifier
        self.highlighting_rules.append((
            re.compile(r'@[a-zA-Z0-9\._]+'),
            self.formats['variable']
        ))

        # References: $identifier
        self.highlighting_rules.append((
            re.compile(r'\$[a-zA-Z0-9\._]+'),
            self.formats['reference']
        ))

        # Numbers (signed)
        self.highlighting_rules.append((
            re.compile(r'[+-]?\d+(?:\.\d+)?'),
            self.formats['number']
        ))

        # Functions: identifier followed by parentheses
        # This is tricky because we need to distinguish from other identifiers
        # We'll look for word followed by optional whitespace and opening paren
        self.highlighting_rules.append((
            re.compile(r'\b[a-zA-Z][a-zA-Z0-9\._]*\s*(?=\()'),
            self.formats['function']
        ))

        # Operators
        self.highlighting_rules.append((
            re.compile(r'->|==|='),
            self.formats['operator']
        ))

        # Brackets and parentheses
        self.highlighting_rules.append((
            re.compile(r'[\[\]()]'),
            self.formats['bracket']
        ))

        # Commas
        self.highlighting_rules.append((
            re.compile(r','),
            self.formats['punctuation']
        ))

    def highlightBlock(self, text):
        """Apply syntax highlighting to a block of text"""

        # Apply each highlighting rule
        for pattern, format in self.highlighting_rules:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format)

        # Handle multi-line comments (this is a simplified approach)
        # In a more sophisticated implementation, you'd track state across blocks
        self._highlight_multiline_comments(text)

    def _highlight_multiline_comments(self, text):
        """Handle comments that might span multiple lines"""
        # This is a basic implementation - for production code you might want
        # to use QSyntaxHighlighter's state management for proper multi-line handling

        # Find unclosed comment starts
        comment_start = text.find('~')
        while comment_start >= 0:
            # Look for the closing ~
            comment_end = text.find('~', comment_start + 1)
            if comment_end >= 0:
                # Complete comment found
                length = comment_end - comment_start + 1
                self.setFormat(comment_start, length, self.formats['comment'])
                comment_start = text.find('~', comment_end + 1)
            else:
                # Unclosed comment - highlight to end of line
                length = len(text) - comment_start
                self.setFormat(comment_start, length, self.formats['comment'])
                break



