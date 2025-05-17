import os
from typing import Callable

from PySide6.QtGui import QPixmap, QPainter, QIcon
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QWidget, QHBoxLayout

from PySide6.QtCore import Qt

from flightpath.widgets.clickable_label import ClickableLabel
from flightpath.util.file_utility import FileUtility as fiut

class IconPackager:

    @classmethod
    def add_svg_icon(cls, *, main, widget:QWidget, on_click:Callable|list[Callable], icon_path:str|list[str]) -> QWidget:
        #
        # if you pass in a list of icon path or callable both must
        # have the same number of elements in the list in the same
        # order. if there is a _clicked version of the icon housed
        # at the same place it will be used for visual feedback on
        # click. ./icons/my_icon.svg would have a feedback icon at
        # ./icons/my_icon_clicked.svg.
        #
        if widget is None:
            raise ValueError("Widget cannot be None")
        if on_click is None:
            raise ValueError("on_click cannot be None")
        if icon_path is None:
            raise ValueError("Icon path cannot be None")
        box = QWidget()
        box_layout = QHBoxLayout(box)
        box_layout.setContentsMargins(0, 0, 0, 0)
        box_layout.addWidget(widget)

        if not isinstance(on_click, list):
            on_click = [on_click]
        if not isinstance(icon_path, list):
            icon_path = [icon_path]

        if not len(icon_path) == len(on_click):
            raise ValueError("You must provide the name number of icons and callbacks")
        for i, path in enumerate(icon_path):
            p = fiut.make_app_path(path, main=main)
            main.log(f"IconPackager: svg icon path: {p}")
            pixmap = cls._make_pixmap(p)
            icon = ClickableLabel(icon_path=p)
            icon.setPixmap(pixmap)
            icon.show()
            box_layout.addWidget(icon)
            icon.icon_pixmap = pixmap
            icon.click_callback = on_click[i]
        return box

    @classmethod
    def _make_pixmap(cls, path:str) -> QPixmap:
        svg_renderer = QSvgRenderer(path)
        if not svg_renderer.isValid():
            print("Failed to load SVG file")
        pixmap = QPixmap(16,16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        svg_renderer.render(painter)
        painter.end()
        return pixmap

    @classmethod
    def make_svg_icon(cls, icon_path:str) -> QWidget:
        if icon_path is None:
            raise ValueError("Icon path cannot be None")
        path = fiut.make_app_path(icon_path)
        pixmap = cls._make_pixmap(path)
        icon = QIcon(pixmap)
        return icon

    @classmethod
    def make_clickable_label(cls, parent, on_click, icon_path:str) -> ClickableLabel:
        if icon_path is None:
            raise ValueError("Icon path cannot be None")
        if on_click is None:
            raise ValueError("on_click cannot be None")
        clk = ClickableLabel(parent)
        clk.setStyleSheet("ClickableLabel { color:#cc9933; }")
        path = fiut.make_app_path(icon_path)
        pixmap = cls._make_pixmap(path)
        clk.setPixmap(pixmap)
        clk.show()
        clk.clicked.connect( on_click )
        return clk



