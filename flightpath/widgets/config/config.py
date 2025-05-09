
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
        #
        # a reload is quick and assures there is a config file. that
        # shouldn't be a concern, given that we have a handle to a
        # config already, tho. the only disconnect might be if a change
        # was made by hand to config.ini and it hadn't been reloaded.
        # that's not a crazy scenario, even if not expected.
        #
        self.main.csvpath_config.reload()
        #
        # ready will go True when the forms are all setup and
        # the toolbar is in its initial state. we'll check ready
        # for any connect callbacks. if those happen during
        # setup pre->ready ==True we'll ignore them.
        #
        self.ready = False
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.toolbar = ConfigToolbar()
        layout.addWidget(self.toolbar)

        self.panels = QWidget(self)
        self.stacked_layout = QStackedLayout()
        self.panels.setLayout(self.stacked_layout)

        self.config_panel = ConfigPanel(main=self.main)
        self.config_panel.setup_forms()
        self.stacked_layout.addWidget(self.config_panel)

        layout.addWidget(self.panels)
        self.setLayout(layout)

        self.show_help_for_form("about")
        #
        # we need to get the buttons in the right states. they
        # potentially change during setup, so this is a good place
        # to true-up.
        #
        self.reset_config_toolbar()
        self.ready = True

    def reset_config_toolbar(self):
        self.toolbar.button_close.setEnabled(True)
        self.toolbar.button_cancel_changes.setEnabled(False)
        self.toolbar.disable_save()


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


