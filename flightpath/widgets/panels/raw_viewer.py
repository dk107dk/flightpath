import sys

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPlainTextEdit, QLabel
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos

from flightpath.util.style_utils import StyleUtility as stut

from flightpath.editable import EditStates

class RawViewer(QWidget):

    def __init__(self, *, main, parent, editable=None):
        super().__init__()
        self.main = main
        self.parent = parent
        #
        # sets the font size
        #
        stut.set_common_style(self)
        #
        #
        #
        self.path = main.selected_file_path
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.text_edit = QPlainTextEdit(self)
        self.text_edit.textChanged.connect(self.on_text_changed)
        self.text_edit.setLineWrapMode(QPlainTextEdit.NoWrap)
        #
        # used by style utility
        #
        self.content_view = self.text_edit

        self.editable = editable if editable is not None else EditStates.UNEDITABLE
        self.text_edit.editable = self.editable
        print(f"Rawviewerx: self.editable: {self.editable}, self.text_edit.editable: {self.text_edit.editable}")
        if self.text_edit.editable:
            self.text_edit.setReadOnly(False)
            stut.set_editable_background(self)
        else:
            self.text_edit.setReadOnly(True)
            #stut.set_editable_background(self.text_edit)

        layout.addWidget(self.label)
        layout.addWidget(self.text_edit)
        self.loaded = False

    def on_text_changed(self) -> None:
        self.parent.mark_unsaved()

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
        self.text_edit.setPlainText(content)
        self.loaded = True

    def clear(self):
        self.main.show_now_or_later(self.text_edit)
        self.text_edit.hide()



