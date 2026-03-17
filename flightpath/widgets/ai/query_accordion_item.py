from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtGui import QColor, QPainter, QBrush
from PySide6.QtCore import Qt, Signal


ACTIVITY_ICONS = {
    "validation": "📄",
    "question": "❓",
    "improve": "🔧",
    "testdata": "🧪",
}


class StatusDot(QWidget):
    def __init__(self, color: QColor, parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(16, 16)

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


class QueryAccordionItem(QWidget):
    clicked = Signal(object)
    closeRequested = Signal(object)

    def __init__(self, title: str, activity: str, status_color: QColor, metadata: dict, parent=None):
        super().__init__(parent)
        self._metadata = metadata

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 4, 8, 4)
        main_layout.setSpacing(2)

        header = QWidget(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        self.status_dot = StatusDot(status_color, header)
        self.icon_label = QLabel(ACTIVITY_ICONS.get(activity, ""), header)
        self.icon_label.setFixedWidth(24)
        self.icon_label.setAlignment(Qt.AlignCenter)

        self.title_label = QLabel(title, header)
        self.title_label.setStyleSheet("font-weight: 500;")

        self.close_button = QPushButton("X", header)
        self.close_button.setFixedSize(22, 22)
        self.close_button.setFocusPolicy(Qt.NoFocus)

        header_layout.addWidget(self.status_dot)
        header_layout.addWidget(self.icon_label)
        header_layout.addWidget(self.title_label, 1)
        header_layout.addWidget(self.close_button)

        main_layout.addWidget(header)

        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        main_layout.addWidget(line)

        header.mousePressEvent = self._on_header_clicked
        self.close_button.clicked.connect(self._on_close_clicked)

    @property
    def metadata(self):
        return self._metadata

    def _on_header_clicked(self, event):
        self.clicked.emit(self._metadata)

    def _on_close_clicked(self):
        self.closeRequested.emit(self._metadata)

