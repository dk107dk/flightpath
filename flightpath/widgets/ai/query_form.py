from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QHBoxLayout, QPlainTextEdit, QScrollArea
)

from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos

from flightpath.widgets.ai.activity_selector import ActivitySelector

class QueryFormWidget(QWidget):
    querySubmitted = Signal(dict)

    def __init__(self, *, parent=None, main):
        super().__init__(parent)
        self.main = main

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # activity selector
        self.activity_selector = ActivitySelector(parent=self, main=main)
        layout.addWidget(self.activity_selector)
        #
        # fields update as needed when selector changes
        #
        self.prompt_title = QLineEdit(self)
        self.prompt_title.setPlaceholderText("Name your request…")
        layout.addWidget(self.prompt_title)
        self.instructions = QPlainTextEdit(self)
        self.instructions.setPlaceholderText("Enter your question or instructions…")
        layout.addWidget(self.instructions)
        #
        # document context checkbox controls doc path visibility
        #
        self.use_doc_checkbox = QCheckBox("Use current document as context", self)
        layout.addWidget(self.use_doc_checkbox)

        self.doc_path = QScrollArea()
        self.doc_path.setWidgetResizable(True)
        self.doc_path.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.doc_path.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.doc_path.setFixedHeight(33)

        self.doc_path_text = QLabel()
        self.doc_path_text.setText("")
        self.doc_path_text.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.doc_path.setWidget(self.doc_path_text)
        layout.addWidget(self.doc_path)

        self.submit_btn = QPushButton("Submit", self)
        layout.addWidget(self.submit_btn)
        #
        # signals
        #
        self.submit_btn.clicked.connect(self._on_submit)
        self.use_doc_checkbox.stateChanged.connect(self.on_use_doc)
        self._current_activity = "validation"
        self.activity_selector.activityChanged.connect(self._on_activity_changed)

    def _on_activity_changed(self, mode: str):
        self._current_activity = mode
        # TODO: show/hide fields depending on mode

    def on_use_doc(self, state:int) -> None:
        if state == Qt.CheckState.Checked.value:
            self.doc_path.show()
            self.doc_path_text.setText(self.main.selected_file_path)
        else:
            self.doc_path.hide()
            self.doc_path_text.setText("")

    def _on_submit(self):
        #
        # get the turns limit from generator.ini
        #
        params = {
            "activity": self._current_activity,
            "title": self.prompt_title.text(),
            "instructions": self.instructions.toPlainText(),
            "use_document": self.use_doc_checkbox.isChecked(),
            #
            #
            #
            "document_path": self.doc_path_text.text() if self.doc_path.isVisible() else None,
            "example": self.get_example_from_path_if(self.doc_path_text.text())
        }
        self.querySubmitted.emit(params)

    def load_params(self, params: dict):
        #
        # we do this when an accordian item is clicked
        #
        self.activity_selector.set_activity(params.get("activity", "create"))
        self.prompt_title.setText(params.get("title", ""))
        self.instructions.setPlainText(params.get("instructions", ""))
        self.use_doc_checkbox.setChecked(bool(params.get("document_path")))
        self.set_document_context(params.get("document_path"))
        #
        # we want to display any feedback we collected in the help & feedback tabs
        # but we'll do that from the query tab where we caught the event.
        #

    def get_example_from_path_if(self, path:str) -> str:
        if Nos(path).exists():
            with DataFileReader(path) as file:
                return file.source.read()
        return ""

    def set_document_context(self, path: str | None):
        if path:
            self.doc_path_text.setText(path)
            self.doc_path.show()
        else:
            self.doc_path.hide()

