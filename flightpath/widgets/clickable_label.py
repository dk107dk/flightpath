import time
from typing import Callable

from PySide6.QtCore import QTimer,Signal
from PySide6.QtGui import QPixmap, QPainter, QIcon, QPaintEvent
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QWidget, QHBoxLayout, QApplication, QLabel
from PySide6.QtCore import Qt

from csvpath.util.nos import Nos

class ClickableLabel(QLabel):

    def __init__(self, parent=None, *, icon_path:str=None) -> None:
        #
        # to get a simple feedback make an icon same as icon_path but
        # with the pre-extension name suffixed with _clicked:
        #    - ./icons/blue.svg
        #    - ./icons/blue_clicked.svg
        #
        super().__init__(parent)
        self._click_callback = None
        self._icon_path = icon_path
        self._icon_pixmap = None
        self._icon_clicked_path = None
        self._icon_clicked_pixmap = None
        self._current_icon_path = self._icon_path
        #
        # we run this timer if we have a feedback icon
        #
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._timeout)
        self.timer_interval = 200
        #
        # if we have a matching clicked icon we use it to make a click
        # feedback.
        #
        if self._icon_path:
            t = self._icon_path[self._icon_path.rfind(".")+1:]
            b = self._icon_path[0:self._icon_path.rfind(".")]
            self._icon_clicked_path = f"{b}_clicked.{t}"

    @property
    def click_callback(self) -> Callable:
        return self._click_callback

    @click_callback.setter
    def click_callback(self, c:Callable) -> None:
        self._click_callback = c

    @property
    def icon_pixmap(self) -> QPixmap:
        return self._icon_pixmap

    @icon_pixmap.setter
    def icon_pixmap(self, pm:QPixmap) -> None:
        self._icon_pixmap = pm

    clicked = Signal(str)

    def _generate_pixmap(self) -> bool:
        if not Nos(self._icon_clicked_path).exists():
            self._icon_clicked_path = None
            return False
        svg_renderer = QSvgRenderer(self._icon_clicked_path)
        if not svg_renderer.isValid():
            print("Failed to load SVG file")
        pixmap = QPixmap(16,16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        svg_renderer.render(painter)
        painter.end()
        self._icon_clicked_pixmap=pixmap
        return True

    def _timeout(self) -> None:
        if self._current_icon_path and self._current_icon_path == self._icon_clicked_path:
            self.setPixmap(self._icon_pixmap)

    def mousePressEvent(self, event):
        self.clicked.emit(self.text())
        #
        # block propagation
        event.accept()
        # super().mousePressEvent(event)
        #
        if self._icon_clicked_path and self._icon_pixmap:
            if not self._icon_clicked_pixmap:
                if not self._generate_pixmap():
                    self._icon_clicked_path = None
            self.setPixmap(self._icon_clicked_pixmap)
            self._current_icon_path = self._icon_clicked_path
            #
            # timer resets the icon in 200ms
            #
            self.timer.start(self.timer_interval)
        if self._click_callback:
            self._click_callback()


