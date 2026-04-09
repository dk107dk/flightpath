from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QStyle,
)
from PySide6.QtGui import QColor, QPainter, QBrush
from PySide6.QtCore import Qt, Signal, QSize

import darkdetect

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

    def __init__(
        self,
        title: str,
        activity: str,
        status_color: QColor,
        metadata: dict,
        parent=None,
    ):
        super().__init__(parent)
        self._metadata = metadata

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 4, 8, 4)
        main_layout.setSpacing(2)

        self.header = QWidget(self)
        self.header.setObjectName("ai_item")
        self.update_style()

        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        self.status_dot = StatusDot(status_color, self.header)
        self.status_dot.setFixedWidth(24)
        self.status_dot.setStyleSheet("StatusDot { padding-left:10px; }")

        self.icon_label = QLabel(ACTIVITY_ICONS.get(activity, ""), self.header)
        self.icon_label.setFixedWidth(24)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("QLabel { border: 0px;background-color:none }")

        self.title_label = QLabel(title, self.header)
        self.title_label.setStyleSheet(
            "font-weight: 500;border:0px;background-color:none; "
        )

        self.close_button = QPushButton()
        self.close_button.setFixedSize(25, 22)
        self.close_button.setFocusPolicy(Qt.NoFocus)
        self.close_button.setStyleSheet(
            "background-color: transparent; border: none; margin: 0 10px 0px 0;"
        )
        pixmapi = QStyle.StandardPixmap.SP_TitleBarCloseButton
        icon = self.close_button.style().standardIcon(pixmapi)
        self.close_button.setIcon(icon)
        self.close_button.setIconSize(QSize(16, 16))

        header_layout.addWidget(self.status_dot)
        header_layout.addWidget(self.icon_label)
        header_layout.addWidget(self.title_label, 1)
        header_layout.addWidget(self.close_button)

        main_layout.addWidget(self.header)

        self.header.mousePressEvent = self._on_header_clicked
        self.close_button.clicked.connect(self._on_close_clicked)
        self._worker = None

    def update_style(self) -> None:
        back = "333" if darkdetect.isDark() else "eee"
        border = "777" if darkdetect.isDark() else "999"
        o = "{"
        c = "}"
        self.header.setStyleSheet(
            f"""
            QWidget#ai_item {o}
                background-color: #{back};
                border: 1px solid #{border};
                border-radius:5px;
                min-height:33px;
                padding:2px 5px 2px 5px;
            {c}""".replace("\n", "")
        )

    @property
    def worker(self) -> AiWorker:
        return self._worker

    @worker.setter
    def worker(self, worker: AiWorker) -> None:
        self._worker = worker

    @property
    def metadata(self):
        return self._metadata

    def _on_header_clicked(self, event):
        self.clicked.emit(self._metadata)

    def _on_close_clicked(self):
        self.closeRequested.emit(self._metadata)
