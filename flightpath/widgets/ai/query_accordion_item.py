from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame, QStyle
)
from PySide6.QtGui import QColor, QPainter, QBrush
from PySide6.QtCore import Qt, Signal, QSize

from flightpath.workers.ai_worker import AiWorker

ACTIVITY_ICONS = {
    "validation": "🪄",
    "question": "✍️",
    "explain": "❓",
    "testdata": "▒",
}


class StatusDot(QWidget):
    def __init__(self, color: QColor, parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(12, 12)

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
        header.setObjectName("ai_item")
        #header.setStyleSheet("QWidget#ai_item { border: 0px; }")
        header.setStyleSheet("""
QWidget#ai_item {
    background-color: #eeeeee;
    border: 1px solid #999;
    border-radius:5px;
    min-height:33px;
    padding:2px 5px 2px 5px;
}""".replace("\n",""))



        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        self.status_dot = StatusDot(status_color, header)
        self.status_dot.setFixedWidth(24)
        self.status_dot.setStyleSheet("StatusDot { padding-left:10px; }")

        self.icon_label = QLabel(ACTIVITY_ICONS.get(activity, ""), header)
        self.icon_label.setFixedWidth(24)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("QLabel { border: 0px;background-color:none }")

        self.title_label = QLabel(title, header)
        self.title_label.setStyleSheet("font-weight: 500;border:0px;background-color:none; ")

        self.close_button = QPushButton()
        self.close_button.setFixedSize(25, 22)
        self.close_button.setFocusPolicy(Qt.NoFocus)
        self.close_button.setStyleSheet("background-color: transparent; border: none; margin: 0 10px 0px 0;")
        pixmapi = QStyle.StandardPixmap.SP_TitleBarCloseButton
        icon = self.close_button.style().standardIcon(pixmapi)
        self.close_button.setIcon(icon)
        self.close_button.setIconSize(QSize(16, 16))

        header_layout.addWidget(self.status_dot)
        header_layout.addWidget(self.icon_label)
        header_layout.addWidget(self.title_label, 1)
        header_layout.addWidget(self.close_button)

        main_layout.addWidget(header)

        #line = QFrame(self)
        #line.setFrameShape(QFrame.HLine)
        #line.setStyleSheet("QFrame { background-color: #999; border: none;height:1px; }")
        #main_layout.addWidget(line)

        header.mousePressEvent = self._on_header_clicked
        self.close_button.clicked.connect(self._on_close_clicked)
        self._worker = None

    @property
    def worker(self) -> AiWorker:
        return self._worker

    @worker.setter
    def worker(self, worker:AiWorker) -> None:
        self._worker = worker

    @property
    def metadata(self):
        return self._metadata

    def _on_header_clicked(self, event):
        self.clicked.emit(self._metadata)

    def _on_close_clicked(self):
        self.closeRequested.emit(self._metadata)

