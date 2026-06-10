from PySide6.QtWidgets import (  # pylint: disable=E0611
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QDialog,
    QWidget,
)
from PySide6.QtCore import Qt  # pylint: disable=E0611


from csvpath.managers.server_config import ServerConfig

from flightpath.dialogs.sftp.sftp_panel import SftpPanel
from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.util.help_finder import HelpFinder


class SftpServersDialog(QDialog):
    def __init__(self, *, main, name, parent, configs: dict[str, ServerConfig]):
        super().__init__(None)
        self.main = main
        self.my_parent = parent
        self.name = name
        self.configs = configs

        self.setWindowTitle(f"Add SFTP Servers For {name}")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.NonModal)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        self.panel = SftpPanel(parent=self, main=self.main, configs=self.configs)
        main_layout.addWidget(self.panel)

        self.method = None
        self.set_button = QPushButton()
        self.set_button.setText("Save")
        self.set_button.clicked.connect(self.do_set)
        self.set_button.setEnabled(False)
        self.cancel_button = QPushButton()
        self.cancel_button.setText("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        #
        self.setFixedHeight(270)
        self.setFixedWidth(760)

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(10, 0, 0, 10)

        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.set_button)

        self.buttons = QWidget()
        self.buttons.setLayout(buttons_layout)
        box = HelpIconPackager.add_help(
            main=self.main, widget=self.buttons, on_help=self.on_help_servers
        )
        # reposition the help icon
        box.setStyleSheet("ClickableLabel {margin-bottom:10px;margin-right:10px;}")

        main_layout.addWidget(box)
        self._populate()

    def do_set(self) -> None:
        print(f"dialog doset: {self.name}, configs: {self.configs}")
        self.my_parent.set_sftps(self.name, self.panel.configs)
        print("dialog doset: done")
        self.close()

    def _populate(self) -> None:
        # if self.configs is not None:
        #    self.panel.populate(self.configs)
        ...

    def on_help_servers(self) -> None:
        md = HelpFinder(main=self.main).help("sftp_servers/other_sftp_servers.md")
        if md is None:
            self.main.helper.close_help()
            return
        self.main.helper.get_help_tab().setMarkdown(md)
        if not self.main.helper.is_showing_help():
            self.main.helper.on_click_help()

    def show_dialog(self) -> None:
        self.show()
