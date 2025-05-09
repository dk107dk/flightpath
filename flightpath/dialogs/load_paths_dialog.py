from PySide6.QtWidgets import ( # pylint: disable=E0611
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QDialog,
        QLineEdit,
        QFormLayout,
        QScrollArea,
)
from PySide6.QtCore import Qt, QFileInfo # pylint: disable=E0611

from csvpath import CsvPaths
from csvpath.util.nos import Nos

from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.util.help_finder import HelpFinder

class LoadPathsDialog(QDialog):

    def __init__(self, *, path, parent):
        super().__init__(parent)
        self.sidebar = parent
        self.csvpaths = CsvPaths()
        self.mgr = self.csvpaths.paths_manager
        self.named_paths_names = self.mgr.named_paths_names

        self.setWindowTitle("Load csvpath files")

        self.path = path
        info = QFileInfo(path)
        self.template_ctl = None
        self.named_paths_name_ctl = None
        #
        # loading named-paths(s) from a json only allows create/overwrite. there
        # is no append option and the user selects the name(s) in the json, not
        # the form. the form simplifies down to basically load or cancel.
        #
        self.json = info.suffix() == "json"
        self.errors = None
        self.template = None
        self.named_paths_name = None
        self.recurse = True

        if self.json:
            self.setFixedHeight(100)
            self.setFixedWidth(650)
        else:
            self.setFixedHeight(200)
            self.setFixedWidth(650)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        self.setWindowModality(Qt.ApplicationModal)

        form_layout = QFormLayout()
        main_layout.addLayout(form_layout)

        file = Nos(self.path).isfile()
        lab = QLabel()
        lab.setText(self.path)

        area = QScrollArea()
        area.setWidget(lab)
        area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        area.setWidgetResizable(False)
        area.setFixedHeight(27)
        area.setStyleSheet("QScrollArea {padding:3px 0 0 0;}")
        area.horizontalScrollBar().setStyleSheet("QScrollBar {height: 0px;}")

        if not self.json:
            self.named_paths_name_ctl = QLineEdit()
            clabel = QLabel()
            clabel.setText("Create or add to named-paths name: ")
            clabel.setWordWrap(True)
            box = HelpIconPackager.add_help(
                main=self.sidebar.main,
                widget=self.named_paths_name_ctl,
                on_help=self.on_help_name
            )
            form_layout.addRow(clabel, box)
            self.named_paths_name_ctl.textChanged.connect(self._name_check)

        if file:
            form_layout.addRow("File to load: ", area)
        else:
            form_layout.addRow("Register files in: ", area)

        if not self.json:
            self.template_ctl = QLineEdit()
            tlabel = QLabel()
            tlabel.setText("Template:")
            box = HelpIconPackager.add_help(main=self.sidebar.main, widget=self.template_ctl, on_help=self.on_help_template)
            form_layout.addRow(tlabel, box)

        self.cancel_button = QPushButton()
        self.cancel_button.setText("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        self.append_button = QPushButton()
        self.append_button.setText("Append")
        self.append_button.clicked.connect(self.sidebar.do_append_named_paths_load)

        self.load_button = QPushButton()
        text = "Create or overwrite" if self.json or not file else "Create"
        self.load_button.setText(text)
        self.load_button.clicked.connect(self.sidebar.do_overwrite_named_paths_load)

        if self.json:
            self.load_button.setEnabled(True)
        else:
            self.append_button.setEnabled(False)
            self.load_button.setEnabled(False)

        buttons = QWidget()
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.cancel_button)
        if not self.json and file is True:
            buttons_layout.addWidget(self.append_button)
        buttons_layout.addWidget(self.load_button)
        buttons.setLayout(buttons_layout)
        main_layout.addWidget(buttons)

    def _name_check(self) -> None:
        t = self.named_paths_name_ctl.text()
        self.load_button.setEnabled(True)
        if t in self.named_paths_names:
            self.append_button.setEnabled(True)
            self.load_button.setText("Overwrite")
        else:
            self.append_button.setEnabled(False)
            self.load_button.setText("Create")

    def on_help_name(self) -> None:
        md = HelpFinder(main=self.sidebar.main).help("load_paths/name.md")
        if md is None:
            self.sidebar.main.helper.close_help()
            return
        self.sidebar.main.helper.get_help_tab().setMarkdown(md)
        if not self.sidebar.main.helper.is_showing_help():
            self.sidebar.main.helper.on_click_help()

    def on_help_template(self) -> None:
        md = HelpFinder(main=self.sidebar.main).help("load_paths/template.md")
        if md is None:
            self.sidebar.main.helper.close_help()
            return
        self.sidebar.main.helper.get_help_tab().setMarkdown(md)
        if not self.sidebar.main.helper.is_showing_help():
            self.sidebar.main.helper.on_click_help()

    def show_dialog(self) -> None:
        self.exec()
