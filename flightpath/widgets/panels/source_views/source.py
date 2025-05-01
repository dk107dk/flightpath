import sys

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPlainTextEdit, QLabel
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos

from flightpath.util.style_utils import StyleUtility as stut


class SourceViewer(QWidget):

    def __init__(self, main):
        super().__init__()
        stut.set_common_style(self)
        self.main = main
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.text_edit.setReadOnly(True)
        #self.text_edit.setFont(QFont("Courier, monospace"))
        layout.addWidget(self.label)
        layout.addWidget(self.text_edit)

    def open_file(self, filepath, lines):
        if lines is None:
            lines = []
        if not Nos(filepath).isfile():
            return
        content = ""

        with DataFileReader(filepath) as file:
            try:
                i = 0
                ls = file.source.readlines()
                for line in ls:
                    if i in lines:
                        content = f"{content}{line}"
                        lines.remove(i)
                    if len(lines) == 0:
                        break
                    i += 1
            except:
                self.label.setText("Error opening file")
                return
        self.label.hide()
        self.text_edit.show()
        self.text_edit.setPlainText(content)

    def clear(self):
        self.label.show()
        self.text_edit.hide()



