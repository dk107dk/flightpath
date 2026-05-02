from PySide6.QtWidgets import (  # pylint: disable=E0611
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QDialog,
    QLineEdit,
    QFormLayout,
)
from PySide6.QtCore import Qt  # pylint: disable=E0611


from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.util.help_finder import HelpFinder
from flightpath.util.tabs_utility import TabsUtility as taut
from flightpath.util.message_utility import MessageUtility as meut


class TemplateDialog(QDialog):
    def __init__(self, *, main, name, parent):
        super().__init__(parent)
        self.main = main
        self.csvpaths = main.csvpaths
        self.sidebar = parent

        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.setWindowTitle(f"Add a Template To {name}")

        self.name = name
        self.set_button = QPushButton()
        self.set_button.setText("Set")
        self.set_button.clicked.connect(self.do_set)
        self.set_button.setEnabled(True)
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
            on_help=self.on_help_template,
        )
        form_layout.addRow("Template: ", box)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.set_button)
        main_layout.addLayout(buttons_layout)

        self.tab = None
        for _ in taut.tabs(main.content.tab_widget):
            if _.objectName().endswith(
                f"{self.name}/definition.json"
            ) or _.objectName().endswith(f"{self.name}\\definition.json"):
                self.tab = _

    def _do_set(self, end: str, mgr) -> None:
        t = self.template_ctl.text()
        t, invalid = TemplateDialog.clean_or_reject(t=t, end=end)
        self.template_ctl.setText(t)
        if invalid is True:
            self.template_ctl.setText("")
            meut.warning2(
                parent=self,
                msg="Invalid template. Setting empty string.",
                title="Invalid",
            )
            return
        mgr.describer.store_template(self.name, t)
        #
        # if we updated the file we need to make sure it's closed before we click on it
        # otherwise segfault.
        #
        if self.tab is not None:
            self.main.content.tab_widget.close_tab(self.tab.objectName())
            self.tab = None
        self.close()

    @classmethod
    def clean_or_reject(self, *, t: str, end: str) -> tuple[str, bool]:
        if end is None:
            raise ValueError("End cannot be None")
        if end[0] != ":":
            raise ValueError("End must start with :")
        if t is None:
            return ("", True)
        t = t.strip()
        t = t.replace("//", "/")
        t = t.replace("\\", "/")
        if t == end or t == f"/{end}" or t == f"\\{end}":
            return ("", False)
        if t == "/" or t == "\\":
            return ("", True)
        if t.find(":/") > -1 or t.find(":\\") > -1:
            return ("", True)
        if t != "" and not t.endswith(f"/{end}"):
            t = f"{t}/{end}"
        if t.count(end) > 1 or (t != "" and t.count(end) == 0):
            return ("", True)
        t = t.lstrip("/")
        if len(t) > 1 and t[0] == ":" and t[1] not in "0123456789":
            return ("", True)
        ts = t.split(":")
        if len(ts) > 0:
            for i, _ in enumerate(ts):
                n = end.lstrip(":")
                if _ == n:
                    continue
                elif _ == "":
                    continue
                elif i > 0 and _[0] not in "0123456789":
                    return ("", True)
        return (t, False)

    def on_help_template(self) -> None:
        md = HelpFinder(main=self.sidebar.main).help("templates/template.md")
        if md is None:
            self.sidebar.main.helper.close_help()
            return
        self.sidebar.main.helper.get_help_tab().setMarkdown(md)
        if not self.sidebar.main.helper.is_showing_help():
            self.sidebar.main.helper.on_click_help()

    def _edit(self) -> None: ...

    def show_dialog(self) -> None:
        self.exec()
