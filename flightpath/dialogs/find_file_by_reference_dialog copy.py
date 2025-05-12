import os
from PySide6.QtWidgets import ( # pylint: disable=E0611
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QDialog,
        QLineEdit,
        QComboBox,
        QScrollArea,
        QWidget,
        QPlainTextEdit,
        QApplication
)

from PySide6.QtGui import QClipboard
from PySide6.QtCore import Qt # pylint: disable=E0611

from csvpath import CsvPaths
from csvpath.util.references.files_reference_finder import FilesReferenceFinder
from csvpath.util.references.results_reference_finder import ResultsReferenceFinder

from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.widgets.icon_packager import IconPackager
from flightpath.util.help_finder import HelpFinder
from flightpath.util.log_utility import LogUtility as lout

class FindFileByReferenceDialog(QDialog):

    def __init__(self, *, main):
        super().__init__(main)
        self.main = main
        self.paths = CsvPaths()

        self.setWindowTitle("Find files by reference")

        self.setFixedHeight(290)
        self.setFixedWidth(780)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        #self.setWindowModality(Qt.ApplicationModal)

        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        #
        # named file name
        #
        ref_line = QWidget()

        ref_line_layout = QHBoxLayout()
        ref_line.setLayout(ref_line_layout)
        main_layout.addWidget(ref_line)

        self.named_x_name = QComboBox()
        ref_line_layout.addWidget(self.named_x_name)
        self.named_x_name.addItem("...")
        self.named_x_name.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.named_x_name.activated.connect(self._on_pick_name)

        self.datatype = QComboBox()
        ref_line_layout.addWidget(self.datatype)
        self.datatype.addItem("...")
        self.datatype.addItem("files")
        self.datatype.addItem("results")
        self.datatype.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.datatype.activated.connect(self._on_pick_datatype)

        self.path = QLineEdit()
        paths = [f"assets{os.sep}icons{os.sep}copy.svg", HelpIconPackager.HELP_ICON]
        on_click = [self._on_copy, self._on_help]

        box = IconPackager.add_svg_icon(main=main, widget=self.path, on_click=on_click, icon_path=paths )
        self.path.textChanged.connect(self._on_pick_name)
        ref_line_layout.addWidget(box)

        self.results = QPlainTextEdit()
        self.results.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        main_layout.addWidget(self.results)

        self.count = QScrollArea()
        self.count.setWidgetResizable(True)
        self.count.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.count.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.count.setFixedHeight(35)

        self.results_description = QLabel()
        self.results_description.setText("")
        self.count.setWidget(self.results_description)

        main_layout.addWidget(self.count)


    def _on_pick_datatype(self) -> None:
        datatype = self.datatype.currentText()
        if datatype == "files":
            self._add_named_files()
        else:
            self._add_named_results()
        self._on_pick_name()

    def _add_named_files(self) -> None:
        mgr = self.paths.file_manager
        named_files = mgr.named_file_names
        self.named_x_name.clear()
        self.named_x_name.addItem("...")
        for name in named_files:
            self.named_x_name.addItem(name)
        self._on_pick_name()

    def _add_named_results(self) -> None:
        mgr = self.paths.results_manager
        named_results = mgr.list_named_results()
        self.named_x_name.clear()
        self.named_x_name.addItem("...")
        for name in named_results:
            self.named_x_name.addItem(name)

    def show_dialog(self) -> None:
        self.exec()

    def _on_copy(self) -> None:
        if not self._can_make_reference():
            print("cannot make reference")
            return
        print("copyingX!")
        r = self._make_reference()
        clipboard = QApplication.instance().clipboard() # Get the clipboard instance
        clipboard.setText(self._make_reference()) # Set the clipboard text

    def _on_help(self) -> None:
        ...

    def _resolve( self, r:str, datatype:str) -> str|list[str]:
        if datatype == "files":
            try:
                finder = FilesReferenceFinder(self.paths, name=r)
                return finder.resolve()
            except Exception as e:
                print(f"Error: {type(e)}: {e}")
                return None
        else:
            try:
                finder = ResultsReferenceFinder(self.paths, name=r)
                return finder.resolve(with_instance=False)
            except Exception as e:
                print(f"Error: {type(e)}: {e}")
                return None

    def _make_reference(self) -> str:
        name = self.named_x_name.currentText()
        datatype = self.datatype.currentText()
        path = self.path.text()
        r = f"${name}.{datatype}.{path}"
        return r

    def _can_make_reference(self) -> bool:
        name = self.named_x_name.currentText()
        datatype = self.datatype.currentText()
        if name == "..." or datatype == "...":
            return False
        return True


    def _on_pick_name(self) -> None:
        name = self.named_x_name.currentText()
        datatype = self.datatype.currentText()
        if not self._can_make_reference():
            self.results.setPlainText("")
            self.results_description.setText("")
            return

        r = self._make_reference()

        res = self._resolve(r, datatype)
        out = ""
        number = 0
        if isinstance(res, list):
            out = "\n".join(res)
            number = len(res)
        elif isinstance(res, str):
            out = res
            number = 1

        self.results.setPlainText(out)
        if out and not out.strip() == "":
            self.results_description.setText(f"  {number} named-{datatype} found with reference {r}")
        else:
            self.results_description.setText("")



