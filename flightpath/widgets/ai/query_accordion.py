from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QApplication
from PySide6.QtGui import QColor
from PySide6.QtCore import Signal

import darkdetect

from flightpath.widgets.ai.query_accordion_item import QueryAccordionItem


class QueryAccordionWidget(QWidget):
    itemClicked = Signal(object)
    itemCloseRequested = Signal(object)
    itemInfoRequested = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.container = QWidget()
        self.vbox = QVBoxLayout(self.container)
        self.vbox.setContentsMargins(2, 2, 2, 2)
        self.vbox.setSpacing(4)
        self.vbox.addStretch(1)

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

        self._items = []
        self.setObjectName("acc")
        self.update_style()

    def beep(self) -> None:
        try:
            QApplication.beep()
        except Exception:
            ...

    def update_style(self) -> None:
        if darkdetect.isDark():
            self.setStyleSheet(
                "QWidget { background-color:#535353;border-top:0px solid #ddd; }"
            )
        else:
            self.setStyleSheet(
                "QWidget { background-color:#fafafa;border-top:0px solid #ddd; }"
            )
        for _ in self.items:
            _.update_style()

    @property
    def items(self) -> list:
        if self._items is None:
            self._items = []
        return self._items

    def add_item(self, title: str, activity: str, status_color: QColor, metadata: dict):
        item = QueryAccordionItem(
            title, activity, status_color, metadata, self.container
        )
        self.vbox.insertWidget(self.vbox.count() - 1, item)
        self._items.append(item)

        item.clicked.connect(self.itemClicked)
        item.closeRequested.connect(self.itemCloseRequested)
        item.infoRequested.connect(self.itemInfoRequested)

        return item

    def remove_item(self, metadata: dict):
        tid = metadata.get("id")
        if tid:
            for item in list(self._items):
                iid = item.metadata.get("id")
                if iid == tid:
                    self._items.remove(item)
                    item.setParent(None)
                    item.deleteLater()
                    break
