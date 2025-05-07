
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QStackedLayout
)

from flightpath.widgets.panels.config_panel import ConfigPanel
from flightpath.widgets.toolbars.config_toolbar import ConfigToolbar
from flightpath.util.help_finder import HelpFinder

class Config(QWidget):

    def __init__(self, main):
        super().__init__()
        self.main = main
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.toolbar = ConfigToolbar()
        layout.addWidget(self.toolbar)

        self.panels = QWidget(self)
        self.stacked_layout = QStackedLayout()
        self.panels.setLayout(self.stacked_layout)

        self.config_panel = ConfigPanel(main=self.main)
        self.stacked_layout.addWidget(self.config_panel)

        layout.addWidget(self.panels)
        self.setLayout(layout)

        self.show_help_for_form("about")

    def show_help_for_form(self, name:str, fallback=None) -> None:
        md = HelpFinder(main=self.main).help(f"config/{name}.md", fallback=fallback)
        if md is None:
            self.close_help()
            return
        self.main.helper.get_help_tab().setMarkdown(md)
        self.show_help()

    def show_help(self) -> None:
        if not self.main.helper.is_showing_help():
            self.main.helper.on_click_help()

    def close_help(self) -> None:
        if self.main.helper.is_showing_help():
            self.main.helper.on_click_help()


