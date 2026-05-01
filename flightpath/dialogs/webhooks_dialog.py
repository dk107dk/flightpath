from PySide6.QtWidgets import (  # pylint: disable=E0611
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QDialog,
    QWidget,
)
from PySide6.QtCore import Qt  # pylint: disable=E0611

from csvpath.managers.paths.paths_describer import Webhook, Webhooks, Header

from flightpath.dialogs.webhooks.webhooks_panel import WebhooksPanel
from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.util.help_finder import HelpFinder
from flightpath.util.listener_utility import ListenerUtility as liut


class WebhooksDialog(QDialog):
    def __init__(self, *, main, name, parent):
        super().__init__(None)
        self.main = main
        self.my_parent = parent
        self.name = name

        self.setWindowTitle(f"Configure Webhooks For {name}")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.NonModal)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.panel = WebhooksPanel(parent=self, main=self.main)
        main_layout.addWidget(self.panel, 1)

        self.method = None
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

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.set_button)

        self.buttons = QWidget()
        self.buttons.setLayout(buttons_layout)
        box = HelpIconPackager.add_help(
            main=self.main, widget=self.buttons, on_help=self.on_help_webhooks
        )
        main_layout.addWidget(box)
        self._populate()

    def do_set(self) -> None:
        mgr = self.main.csvpaths.paths_manager
        c = mgr.describer.get_webhooks(self.name)
        if c is None:
            raise ValueError("Webhooks config cannot be None")
        hooks = Webhooks()
        hooks.on_complete_all = self._form_to_webhook(self.panel.forms[0])
        hooks.on_complete_valid = self._form_to_webhook(self.panel.forms[1])
        hooks.on_complete_invalid = self._form_to_webhook(self.panel.forms[2])
        hooks.on_complete_error = self._form_to_webhook(self.panel.forms[3])
        mgr.describer.store_webhooks(self.name, hooks)
        liut.assure_webhooks(self.main)
        self.close()

    def _form_to_webhook(self, form) -> Webhook:
        webhook = Webhook()
        webhook.url = form.url.text()
        webhook.payload = self._payload(form)
        webhook.headers = self._headers(form)
        return webhook

    def _payload(self, form) -> str:
        payload = []
        rows = form.params_table.rowCount()
        for row in range(0, rows):
            n = form.params_table.item(row, 0)
            v = form.params_table.item(row, 1)
            payload.append(f"{n.text()} > {v.text()}")
        return ",".join(payload)

    def _headers(self, form) -> str:
        headers = []
        rows = form.headers_table.rowCount()
        for row in range(0, rows):
            n = form.headers_table.item(row, 0)
            v = form.headers_table.item(row, 1)
            header = Header()
            header.name = n.text()
            header.value = v.text()
            headers.append(header)
        return headers

    def _populate(self) -> None:
        mgr = self.main.csvpaths.paths_manager
        webhooks = mgr.describer.get_webhooks(self.name)
        if webhooks is None:
            raise ValueError("Webhooks config cannot be None")
        forms = self.panel.forms

        webhook = webhooks.on_complete_all
        self._populate_webhook(forms[0], webhook, "all")

        webhook = webhooks.on_complete_valid
        self._populate_webhook(forms[1], webhook, "valid")

        webhook = webhooks.on_complete_invalid
        self._populate_webhook(forms[2], webhook, "invalid")

        webhook = webhooks.on_complete_error
        self._populate_webhook(forms[3], webhook, "error")

    def _populate_webhook(self, form, webhook, name=None) -> None:
        if webhook is None:
            return
        url = webhook.url
        payload = webhook.payload
        if url is not None:
            form.url.setText(url)
        if payload:
            ps = payload.split(",")
            for _ in ps:
                nv = _.split(">")
                form.add_value(form.params_table, nv[0], nv[1])
        for header in webhook.headers:
            form.add_value(form.headers_table, header.name, header.value)

    def on_help_webhooks(self) -> None:
        md = HelpFinder(main=self.main).help("webhooks/webhooks.md")
        if md is None:
            self.main.helper.close_help()
            return
        self.main.helper.get_help_tab().setMarkdown(md)
        if not self.main.helper.is_showing_help():
            self.main.helper.on_click_help()

    def show_dialog(self) -> None:
        self.show()
