from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPlainTextEdit,
    QLabel,
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QFileInfo

from csvpath.util.file_readers import DataFileReader

from flightpath.widgets.csvpath_text_edit import CsvPathTextEdit
from flightpath.actions.run_one_csvpath import RunOneCsvpath
from flightpath.util.syntax.csvpath_highlighter import CsvPathSyntaxHighlighter
from flightpath.util.style_utils import StyleUtility as stut
from flightpath.util.os_utility import OsUtility as osut
from flightpath.util.editable import EditStates


class CsvpathViewer(QWidget):
    def __init__(self, *, main, editable=EditStates.EDITABLE):
        super().__init__()
        self.main = main
        self.editable = editable
        #
        # sets the font size
        #
        stut.set_common_style(self)
        #
        #
        #
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.saved = True
        self.mdata = None
        self._comment = None
        self.path = None
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.text_edit = CsvPathTextEdit(main=main, parent=self, editable=self.editable)
        self.content_view = self.text_edit

        self.text_edit.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.text_edit.setReadOnly(editable == EditStates.UNEDITABLE)
        self.text_edit.setFont(QFont("Courier, monospace"))
        stut.set_editable_background(self.text_edit)

        layout.addWidget(self.label)
        layout.addWidget(self.text_edit)
        layout.setContentsMargins(0, 0, 0, 0)

        self.run_one = RunOneCsvpath(main=self.main)

    def reset_saved(self) -> None:
        self.saved = True
        i = self.main.content.tab_widget.currentIndex()
        name = self.main.content.tab_widget.tabText(i)
        name = name.replace("+", "")
        self.main.content.tab_widget.setTabText(i, name)

    def open_file(self, *, path: str, data: str) -> None:
        self.path = path
        info = QFileInfo(path)
        if info.suffix() not in self.main.csvpath_config.get(
            section="extensions", name="csvpath_files"
        ):
            self.main.show_now_or_later(self.label)
            self.text_edit.hide()
            return
        self.text_edit.clear()
        if data is None:
            with DataFileReader(path) as file:
                data = file.source.read()

        self.label.hide()
        CsvPathSyntaxHighlighter(self.text_edit.document())

        self.main.show_now_or_later(self.text_edit)
        self.text_edit.setPlainText(data)
        c = "cmd" if osut.is_mac() else "ctrl"
        self.main.statusBar().showMessage(
            f"{c}-s to save, {c}-r to run • Opened {path}"
        )
