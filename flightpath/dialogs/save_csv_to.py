import os
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QDialogButtonBox,
)
from PySide6.QtCore import QSize, Qt
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.util.help_finder import HelpFinder


class SaveCsvToDialog(QDialog):
    def __init__(self, *, parent=None, main, path):
        super().__init__(parent)
        self.my_parent = parent
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.NonModal)

        self.main = main
        self.path = path
        name = os.path.basename(path)
        self.setWindowTitle(f"Save {name} to CSV")
        self.setFixedSize(QSize(520, 150))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)
        self.path_ctrl = QLineEdit()
        self.path_ctrl.setText(self.path)
        layout.addWidget(self.path_ctrl)

        form = QWidget()
        form_layout = QFormLayout()
        form_layout.setContentsMargins(3, 3, 3, 3)
        form_layout.setSpacing(6)
        form.setLayout(form_layout)
        layout.addWidget(form)

        self.delimiter = QComboBox()
        self.delimiter.setFixedSize(140, 27)
        self.delimiter.addItems(["Comma", "Pipe", "Semi-colon", "Tab"])
        self.delimiter.currentTextChanged.connect(self.on_delimiter_change)

        self.quotechar = QComboBox()
        self.quotechar.setFixedSize(140, 27)
        self.quotechar.addItems(["Double quotes", "Single quotes"])

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        box = HelpIconPackager.add_help(
            main=self.main, widget=buttons, on_help=self.on_help
        )
        form_layout.addRow("Delimiter: ", self.delimiter)
        form_layout.addRow("Quotechar: ", self.quotechar)
        layout.addWidget(box)  # , alignment=Qt.AlignLeft

        # self.path_ctrl.textChanged.connect(self._show_hide)

    #
    # do we want this? we're always saving to csv.
    #
    def _show_hide(self) -> None:
        if self.path_ctrl.text().endswith(".csv"):
            self.delimiter.setEnabled(True)
            self.quotechar.setEnabled(True)
        else:
            self.delimiter.setEnabled(False)
            self.quotechar.setEnabled(False)

    def on_help(self) -> None:
        md = HelpFinder(main=self.main).help("jsonl/save_as.md")
        if md is None:
            self.main.helper.close_help()
            return
        self.main.helper.get_help_tab().setMarkdown(md)
        if not self.main.helper.is_showing_help():
            self.main.helper.on_click_help()

    def on_delimiter_change(self) -> None:
        path = self.get_path()

        d = self.get_delimiter()
        if d == "Pipe":
            d = "psv"
        elif d == "Semi-colon":
            d = "ssv"
        elif d == "Tab":
            d = "tsv"
        elif d == "Comma":
            d = "csv"

        if not path.endswith(d):
            path = f"{path}.{d}"
            self.path_ctrl.setText(path)

    def _save(self) -> None:
        t = self.get_path()
        delimiter = self.get_delimiter()
        exts = []
        exts.append("csv")
        if delimiter == "Comma":
            ...
        elif delimiter == "Pipe":
            exts.append("psv")
        elif delimiter == "Semi-colon":
            exts.append("ssv")
        elif delimiter == "Tab":
            exts.append("tsv")
        quotechar = self.get_quotechar()
        d = os.path.dirname(t)
        b = os.path.basename(t)
        t = fiut.deconflicted_path(d, b)
        self.my_parent._save_one_of(
            path=t, delimiter=delimiter, quotechar=quotechar, exts=exts
        )
        self.accept()

    def get_path(self) -> str:
        return self.path_ctrl.text()

    def get_delimiter(self) -> str:
        return self.delimiter.currentText()

    def get_quotechar(self) -> str:
        return self.quotechar.currentText()
