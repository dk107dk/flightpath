import sys

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPlainTextEdit, QLabel
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos

from flightpath.util.style_utils import StyleUtility as stut

from flightpath.editable import EditStates

class RawViewer(QWidget):

    def __init__(self, main):
        super().__init__()
        #
        # sets the font size
        #
        stut.set_common_style(self)
        #
        #
        #
        self.main = main
        self.path = main.selected_file_path
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.text_edit = QPlainTextEdit(self)
        self.content_view = self.text_edit
        self.editable = EditStates.UNEDITABLE
        self.text_edit.editable = self.editable
        stut.set_editable_background(self.text_edit)

        self.text_edit.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.label)
        layout.addWidget(self.text_edit)
        self.loaded = False

    def open_file(self, filepath, lines_to_take=None):
        if not Nos(filepath).isfile():
            return
        content = ""
        with DataFileReader(filepath) as file:
            try:
                i = 0
                ls = file.source.readlines()
                for line in ls:
                    if lines_to_take is None or i in lines_to_take:
                        content = f"{content}{line}"
                        if lines_to_take:
                            lines_to_take.remove(i)
                    if lines_to_take and len(lines_to_take) == 0:
                        break
                    i += 1
            except Exception as e:
                self.label.setText(f"Error opening file: {type(e)}: {e}")
                return
        self.label.hide()
        self.main.show_now_or_later(self.text_edit)
        #self.text_edit.show()
        self.text_edit.setPlainText(content)
        self.loaded = True

    def clear(self):
        self.main.show_now_or_later(self.text_edit)
        #self.label.show()
        self.text_edit.hide()



