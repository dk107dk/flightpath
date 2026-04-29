from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QStyle,
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, Signal, QSize

import darkdetect

from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata

from flightpath.workers.ai_worker import AiWorker
from .status_dot import StatusDot


class QueryAccordionItem(QWidget):
    ACTIVITY_ICONS = {
        "validation": "🪄",
        "question": "✍️",
        "explain": "❓",
        "testdata": "▒",
        "run": "⚙️",
    }
    ACTIVITY_NAMES = {
        "validation": "Create a validation based on example data",
        "question": "Answer a CsvPath question",
        "explain": "Describe how a validation script works",
        "testdata": "Generate test CSV data based on a validation script",
        "run": "Run a group of csvpath statements",
    }

    #
    # the label and close button work like:
    #    item.button->item.signal
    #      item.signal->emit->accordian.slot
    #        accordian.signal->emit->container slot on method that reacts
    #
    # clicked         == a click on the title
    # closeRequested  == click on the x to dismiss the item from the
    #                    list
    # infoRequested   == click the status icon to open info about the
    #                    running process
    #
    clicked = Signal(object)
    closeRequested = Signal(dict)
    infoRequested = Signal(dict)

    def __init__(
        self,
        *,
        title: str,
        activity: str,
        status_color: QColor,
        metadata: dict,
        parent=None,
        status: str = "pending",
        subtitle: str = "",
    ):
        super().__init__(parent)
        self._metadata = metadata
        #
        # this is here for csvpath, but should be unnecessary soon:
        #        /csvpath/managers/registrar.py", line 37, in add_internal_listener
        #            if not lst.config:
        #
        self.config = None  # keep for listening to csvpath registrars
        self.csvpaths = None  # here for listening to csvpath registrars
        #
        #
        #
        self.status = None
        #
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

        self.icon_label = None
        if str(activity).strip() != "":
            self.icon_label = QLabel(
                QueryAccordionItem.ACTIVITY_ICONS.get(activity, ""), self.header
            )
            self.icon_label.setFixedWidth(24)
            self.icon_label.setAlignment(Qt.AlignCenter)
            self.icon_label.setStyleSheet(
                "QLabel { border: 0px;background-color:none }"
            )
            self.icon_label.setToolTip(QueryAccordionItem.ACTIVITY_NAMES.get(activity))
        #
        # title and subtitle, if any
        #
        atitle = None
        if title is None:
            title = ""
        atitle = QWidget()
        atitle.setObjectName("title")
        title_layout = QVBoxLayout()
        atitle.setStyleSheet("border:0px;background-color:none;")
        self.title = QLabel(title)
        self.title.setStyleSheet(
            "font-weight: 500;font-size:12pt;border:0px;background-color:none;"
        )
        title_layout.addWidget(self.title)
        if str(subtitle).strip() in ["", "None"] and subtitle in metadata:
            subtitle = metadata["subtitle"]
        self.subtitle = QLabel(subtitle)
        self.subtitle.setStyleSheet(
            "font-weight:300;font-size:10pt;font-style:italic;border:0px;background-color:none;"
        )
        title_layout.addWidget(self.subtitle)
        atitle.setLayout(title_layout)

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
        if self.icon_label is not None:
            header_layout.addWidget(self.icon_label)
        header_layout.addWidget(atitle, 1)
        header_layout.addWidget(self.close_button)

        main_layout.addWidget(self.header)

        self.header.mousePressEvent = self._on_header_clicked
        self.close_button.clicked.connect(self._on_close_clicked)
        self.status_dot.clicked.connect(self._on_status_clicked)
        self._worker = None
        self._listeners: list[Listener] = []

    def add_listener(self, lst: Listener) -> None:
        self._listeners.append(lst)

    def metadata_update(self, mdata: Metadata) -> None:
        for _ in self._listeners:
            _.metadata_update(mdata)

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

    def _on_status_clicked(self):
        self.infoRequested.emit(self._metadata)
