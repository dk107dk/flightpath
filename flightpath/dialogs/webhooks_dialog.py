from PySide6.QtWidgets import (  # pylint: disable=E0611
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QDialog,
    QLineEdit,
    QFormLayout,
    QGroupBox,
    QWidget,
)
from PySide6.QtCore import Qt  # pylint: disable=E0611

from csvpath.managers.paths.paths_describer import Webhook

from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.util.help_finder import HelpFinder


class WebhooksDialog(QDialog):
    def __init__(self, *, main, name, parent):
        super().__init__(None)
        self.main = main
        self.csvpaths = main.csvpaths
        self.sidebar = parent

        self.setWindowTitle(f"Configure webhooks for {name}")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.NonModal)

        self.method = None
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
        self.setFixedHeight(480)
        self.setFixedWidth(780)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.all_url = QLineEdit()
        self.valid_url = QLineEdit()
        self.invalid_url = QLineEdit()
        self.error_url = QLineEdit()
        self.on_complete_all = QLineEdit()
        self.on_complete_valid = QLineEdit()
        self.on_complete_invalid = QLineEdit()
        self.on_complete_error = QLineEdit()

        self.all_url.setFixedHeight(24)
        self.on_complete_all.setFixedHeight(24)

        self.valid_url.setFixedHeight(24)
        self.on_complete_valid.setFixedHeight(24)

        self.invalid_url.setFixedHeight(24)
        self.on_complete_invalid.setFixedHeight(24)

        self.error_url.setFixedHeight(24)
        self.on_complete_error.setFixedHeight(24)

        self.on_complete_all.textChanged.connect(self._edit)
        self.on_complete_valid.textChanged.connect(self._edit)
        self.on_complete_invalid.textChanged.connect(self._edit)
        self.on_complete_error.textChanged.connect(self._edit)

        self.all_url.textChanged.connect(self._edit)
        self.valid_url.textChanged.connect(self._edit)
        self.invalid_url.textChanged.connect(self._edit)
        self.error_url.textChanged.connect(self._edit)

        self.allbox = QGroupBox("After all runs")
        form_layout = QFormLayout()
        form_layout.addRow("URL: ", self.all_url)
        form_layout.addRow("Properties: ", self.on_complete_all)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        self.allbox.setLayout(form_layout)
        main_layout.addWidget(self.allbox)

        self.validbox = QGroupBox("After valid runs")
        form_layout = QFormLayout()
        form_layout.addRow("URL: ", self.valid_url)
        form_layout.addRow("Properties: ", self.on_complete_valid)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        self.validbox.setLayout(form_layout)
        main_layout.addWidget(self.validbox)

        self.invalidbox = QGroupBox("After invalid runs")
        form_layout = QFormLayout()
        form_layout.addRow("URL: ", self.invalid_url)
        form_layout.addRow("Properties: ", self.on_complete_invalid)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        self.invalidbox.setLayout(form_layout)
        main_layout.addWidget(self.invalidbox)

        self.errorbox = QGroupBox("After runs with errors")
        form_layout = QFormLayout()
        form_layout.addRow("URL: ", self.error_url)
        form_layout.addRow("Properties: ", self.on_complete_error)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        self.errorbox.setLayout(form_layout)
        main_layout.addWidget(self.errorbox)

        self._populate()

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.set_button)

        self.buttons = QWidget()
        self.buttons.setLayout(buttons_layout)
        box = HelpIconPackager.add_help(
            main=self.sidebar.main, widget=self.buttons, on_help=self.on_help_webhooks
        )
        main_layout.addWidget(box)

    def do_set(self) -> None:
        mgr = self.csvpaths.paths_manager
        c = mgr.describer.get_webhooks(self.name)
        if c is None:
            raise ValueError("Webhooks config cannot be None")

        c.on_complete_all = Webhook(
            payload=self.on_complete_all.text(), url=self.all_url.text()
        )
        c.on_complete_valid = Webhook(
            payload=self.on_complete_valid.text(), url=self.valid_url.text()
        )
        c.on_complete_invalid = Webhook(
            payload=self.on_complete_invalid.text(), url=self.invalid_url.text()
        )
        c.on_complete_error = Webhook(
            payload=self.on_complete_error.text(), url=self.error_url.text()
        )

        mgr.describer.store_webhooks(self.name, c)
        self.close()

    def _populate(self) -> None:
        mgr = self.csvpaths.paths_manager
        c = mgr.describer.get_webhooks(self.name)
        if c is None:
            raise ValueError("Webhooks config cannot be None")

        a = c.on_complete_all.url if c.on_complete_all else ""
        v = c.on_complete_valid.url if c.on_complete_valid else ""
        i = c.on_complete_invalid.url if c.on_complete_invalid else ""
        e = c.on_complete_error.url if c.on_complete_error else ""
        self.all_url.setText(a)
        self.valid_url.setText(v)
        self.invalid_url.setText(i)
        self.error_url.setText(e)

        a = c.on_complete_all.payload if c.on_complete_all else ""
        v = c.on_complete_valid.payload if c.on_complete_valid else ""
        i = c.on_complete_invalid.payload if c.on_complete_invalid else ""
        e = c.on_complete_error.payload if c.on_complete_error else ""

        self.on_complete_all.setText(a)
        self.on_complete_valid.setText(v)
        self.on_complete_invalid.setText(i)
        self.on_complete_error.setText(e)

    def on_help_webhooks(self) -> None:
        md = HelpFinder(main=self.sidebar.main).help("webhooks/webhooks.md")
        if md is None:
            self.sidebar.main.helper.close_help()
            return
        self.sidebar.main.helper.get_help_tab().setMarkdown(md)
        if not self.sidebar.main.helper.is_showing_help():
            self.sidebar.main.helper.on_click_help()

    def _edit(self) -> None:
        ...
        #
        # we have to enable removing webhooks by saving ""
        #
        """
        if self._any_and_no_stragglers():
            self.set_button.setEnabled(True)
        else:
            self.set_button.setEnabled(False)
        """

    def _any_and_no_stragglers(self) -> bool:
        t = False

        u = self.all_url.text()
        p = self.on_complete_all.text()
        if (u and not p) or (p and not u):
            return False
        elif u and p:
            t = True

        u = self.valid_url.text()
        p = self.on_complete_valid.text()
        if (u and not p) or (p and not u):
            return False
        elif u and p:
            t = True

        u = self.invalid_url.text()
        p = self.on_complete_invalid.text()
        if (u and not p) or (p and not u):
            return False
        elif u and p:
            t = True

        u = self.error_url.text()
        p = self.on_complete_error.text()
        if (u and not p) or (p and not u):
            return False
        elif u and p:
            t = True

        return t

    def show_dialog(self) -> None:
        self.show()
