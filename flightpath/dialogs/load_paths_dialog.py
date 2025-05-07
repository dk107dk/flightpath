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
from PySide6.QtCore import Qt # pylint: disable=E0611

from csvpath.util.nos import Nos

from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.util.help_finder import HelpFinder

class LoadPathsDialog(QDialog):

    def __init__(self, *, path, parent):
        super().__init__(parent)
        self.sidebar = parent

        self.setWindowTitle("Load csvpath files")

        self.path = path
        self.errors = None
        self.template = None
        self.named_paths_name = None
        self.recurse = True

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


        if file:
            form_layout.addRow("Csvpaths file to load: ", area)
        else:
            form_layout.addRow("Register files within: ", area)

        # foods/:1/data/:0/:filename
        self.template_ctl = QLineEdit()

        tlabel = QLabel()
        tlabel.setText("Template:")
        box = HelpIconPackager.add_help(main=self.sidebar.main, widget=self.template_ctl, on_help=self.on_help_template)
        form_layout.addRow(tlabel, box)


        self.load_button = QPushButton()
        self.load_button.setText(self.tr("Load"))
        self.load_button.clicked.connect(self.sidebar.do_load)
        self.cancel_button = QPushButton()
        self.cancel_button.setText(self.tr("Cancel"))
        self.cancel_button.clicked.connect(self.reject)

        #
        # added the QWidget
        #
        buttons = QWidget()
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.load_button)
        buttons.setLayout(buttons_layout)
        main_layout.addWidget(buttons)


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
