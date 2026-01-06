from PySide6.QtWidgets import QWidget, QPlainTextEdit, QTextEdit
from PySide6.QtCore import QSize, QRect, Qt
from PySide6.QtGui import QColor, QPainter, QTextFormat, QFontDatabase, QTextBlockFormat, QTextCursor, QKeyEvent

from flightpath.editable import EditStates
from flightpath.widgets.editor.syntax import JsonHighlighter
from flightpath.util.style_utils import StyleUtility as stut

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(parent=editor)
        self.codeEditor = editor
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.setFont(font)

    def sizeHint(self):
        return QSize(self.codeEditor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.codeEditor.line_number_area_paint_event(event)


class Editor(QPlainTextEdit):
    def __init__(self, parent=None, *, editable=EditStates.EDITABLE):
        super().__init__(parent)
        self.highlighter = JsonHighlighter(self.document())
        self.line_error = 0
        self.editable = editable
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.setFont(font)

        self.error_format = QTextBlockFormat()
        line_error = QColor(Qt.GlobalColor.red).lighter(180)
        self.error_format.setBackground(line_error)
        stut.set_editable_background(self)

        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width()
        self.highlight_current_line()


    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            super().keyPressEvent(event)
            return
        if self.parentWidget().editable == EditStates.UNEDITABLE:
            return
        else:
            self.parentWidget()._set_modified(True)
        super().keyPressEvent(event)
        cursor: QTextCursor = self.textCursor()
        line = cursor.blockNumber()
        column = cursor.positionInBlock()
        msg = f"[{line+1}, {column}]"
        self.parentWidget().main.statusBar().showMessage(msg)




    def line_number_area_paint_event(self, event):
        painter = QPainter(self.lineNumberArea)
        color = QColor(stut.get_not_editable_color_2())
        if self.editable == EditStates.UNEDITABLE:
            color = color.darker(100)
        painter.fillRect(event.rect(), color)
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.GlobalColor.gray)
                # Start writing the line numbers to give enough margin between the border and the text
                painter.drawText(-5,
                                 top,
                                 self.lineNumberArea.width(),
                                 self.fontMetrics().height(),
                                 Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def set_line_error(self, line_number=0):
        self.line_error = line_number

    def line_number_area_width(self):
        # digits = len(str(self.blockCount()))
        digits = 7  # Fixed gutter size
        # TODO: improve calculation for gutter
        space = 3 + self.fontMetrics().horizontalAdvance('9')*digits
        return space

    def resizeEvent(self, event):
        QPlainTextEdit.resizeEvent(self, event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def update_line_number_area_width(self):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def background_changed(self) -> None:
        self.highlighter = JsonHighlighter(self.document())
        self.highlighter.set_colors()
        self.highlighter.setup_highlight()
        self.highlight_current_line()

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(stut.get_highlight_text())
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            current_line = selection.cursor.blockNumber() + 1
            selection.cursor.clearSelection()
            if self.line_error != current_line:
                extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def highlight_error_line(self, line_number):
        self.line_error = line_number
        line_number -= 1
        cursor = QTextCursor(self.document().findBlockByNumber(line_number))
        cursor.setBlockFormat(self.error_format)
        self.highlight_current_line()  # In case the cursor is on the error line

    def update_line_number_area(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width()
