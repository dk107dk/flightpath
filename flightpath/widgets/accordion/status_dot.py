from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QColor, QPainter, QBrush
from PySide6.QtCore import Qt, Signal


class StatusDot(QWidget):
    def __init__(self, color: QColor, parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(12, 12)

    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

    def setColor(self, color: QColor):
        self._color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(self._color))
        painter.setPen(Qt.NoPen)
        r = min(self.width(), self.height()) - 2
        painter.drawEllipse((self.width() - r) / 2, (self.height() - r) / 2, r, r)
