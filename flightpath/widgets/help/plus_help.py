import os

from PySide6.QtWidgets import QWidget, QHeaderView
from PySide6.QtCore import Qt

from flightpath.widgets.clickable_label import ClickableLabel
from flightpath.widgets.icon_packager import IconPackager
from flightpath.util.file_utility import FileUtility as fiut

class HelpIconPackager:

    HELP_ICON = f"assets{os.sep}icons{os.sep}help.svg"

    @classmethod
    def add_help(cls, *, main, widget:QWidget, on_help) -> QWidget:
        return IconPackager.add_svg_icon(main=main, widget=widget, on_click=on_help, icon_path=HelpIconPackager.HELP_ICON)

    @classmethod
    def make_help_icon(self) -> QWidget:
        return IconPackager.make_svg_icon(HelpIconPackager.HELP_ICON)

    @classmethod
    def make_clickable_label(self, parent, on_help=None) -> ClickableLabel:
        return IconPackager.make_clickable_label(parent, on_help, HelpIconPackager.HELP_ICON)

class HelpHeaderView(QHeaderView):
    def __init__(self, parent=None, *, on_help):
        super().__init__(Qt.Horizontal, parent)
        self.help_icon_label = HelpIconPackager.make_clickable_label(self, on_help=on_help)
        self.help_icon_label.setToolTip("Click here for help")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.help_icon_label.move(self.width() - 25, 3)

