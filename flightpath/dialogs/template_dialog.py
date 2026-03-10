from PySide6.QtWidgets import ( # pylint: disable=E0611
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QDialog,
        QLineEdit,
        QFormLayout,
        QSizePolicy,
        QWidget
)
from PySide6.QtCore import Qt # pylint: disable=E0611

from csvpath import CsvPaths

from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.util.help_finder import HelpFinder
from flightpath.util.tabs_utility import TabsUtility as taut

class TemplateDialog(QDialog):


    def __init__(self, *, main, name, parent):
        super().__init__(parent)
        self.main = main
        self.csvpaths = main.csvpaths
        self.sidebar = parent
        self.setWindowTitle(f"Add a template to {name}")

        self.method = None
        self.name = name
        self.set_button = QPushButton()
        self.set_button.setText("Set")
        self.set_button.clicked.connect(self.do_set)
        self.set_button.setEnabled(False)
        self.cancel_button = QPushButton()
        self.cancel_button.setText("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        #
        #
        #
        self.setFixedHeight(80)
        self.setFixedWidth(450)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.NonModal)

        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        main_layout.addLayout(form_layout)

        self.template_ctl = QLineEdit()
        self.template_ctl.textChanged.connect(self._edit)

        box = HelpIconPackager.add_help(
            main=self.sidebar.main,
            widget=self.template_ctl,
            on_help=self.on_help_template
        )
        form_layout.addRow("Template: ", box)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.set_button)
        main_layout.addLayout(buttons_layout)

        self.tab = None
        for _ in taut.tabs(main.content.tab_widget):
            if ( _.objectName().endswith(f"{self.name}/definition.json")
                or _.objectName().endswith(f"{self.name}\\definition.json") ):
                self.tab = _

    def on_help_template(self) -> None:
        md = HelpFinder(main=self.sidebar.main).help("templates/template.md")
        if md is None:
            self.sidebar.main.helper.close_help()
            return
        self.sidebar.main.helper.get_help_tab().setMarkdown(md)
        if not self.sidebar.main.helper.is_showing_help():
            self.sidebar.main.helper.on_click_help()

    def _edit(self) -> None:
        t = self.template_ctl.text()
        if t and t.strip() != "":
            self.set_button.setEnabled(True)
        else:
            self.set_button.setEnabled(False)

    def show_dialog(self) -> None:
        self.exec()
        #self.show()

