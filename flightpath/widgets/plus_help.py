import os

from PySide6.QtGui import QPixmap, QPainter, QIcon
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QWidget, QHBoxLayout, QHeaderView
from PySide6.QtCore import Qt

from flightpath.widgets.clickable_label import ClickableLabel
from flightpath.util.file_utility import FileUtility as fiut

class HelpIconPackager:

    @classmethod
    def add_help(cls, *, main, widget:QWidget, on_help) -> QWidget:
        box = QWidget()
        box_layout = QHBoxLayout(box)
        box_layout.setContentsMargins(0, 0, 0, 0)
        help = ClickableLabel()
        svg_renderer = QSvgRenderer(fiut.make_app_path(f"assets{os.sep}icons{os.sep}help.svg"))
        if not svg_renderer.isValid():
            print("Failed to load SVG file")
        pixmap = QPixmap(16,16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        svg_renderer.render(painter)
        painter.end()
        help.setPixmap(pixmap)
        help.show()
        box_layout.addWidget(widget)
        box_layout.addWidget(help)
        #
        # connect clicks
        #
        help.clicked.connect( on_help )
        return box

    @classmethod
    def make_help_icon(self) -> QWidget:
        svg_renderer = QSvgRenderer(fiut.make_app_path(f"assets{os.sep}icons{os.sep}help.svg"))
        if not svg_renderer.isValid():
            print("Failed to load SVG file")
        pixmap = QPixmap(16,16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        svg_renderer.render(painter)
        painter.end()
        help = QIcon(pixmap)
        return help

    @classmethod
    def make_clickable_label(self, parent, on_help=None) -> ClickableLabel:
        help = ClickableLabel(parent)
        help.setStyleSheet("ClickableLabel { color:#cc9933; }")
        svg_renderer = QSvgRenderer(fiut.make_app_path(f"assets{os.sep}icons{os.sep}help.svg"))
        if not svg_renderer.isValid():
            print("Failed to load SVG file")
        pixmap = QPixmap(16,16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        svg_renderer.render(painter)
        painter.end()
        help.setPixmap(pixmap)
        help.show()
        if on_help:
            help.clicked.connect( on_help )
        return help


class HelpHeaderView(QHeaderView):
    def __init__(self, parent=None, *, on_help):
        super().__init__(Qt.Horizontal, parent)
        self.help_icon_label = HelpIconPackager.make_clickable_label(self, on_help=on_help)
        self.help_icon_label.setToolTip("Click here for help")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.help_icon_label.move(self.width() - 25, 3)

