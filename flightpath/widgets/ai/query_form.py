from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QPlainTextEdit,
    QComboBox,
    QFormLayout,
    QScrollArea,
)

from csvpath.util.file_readers import DataFileReader

from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.widgets.ai.activity_selector import ActivitySelector
from flightpath.util.help_finder import HelpFinder
from flightpath.util.tdata_utility import TDataUtility as tdut
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.generator_utility import GeneratorUtility as geut
from flightpath.widgets.panels.csvpath_viewer import CsvpathViewer


class QueryFormWidget(QWidget):
    querySubmitted = Signal(dict)

    def __init__(self, *, parent=None, main):
        super().__init__(parent)
        self.main = main
        self.my_parent = parent

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
        self.prompt_title.textChanged.connect(self.on_prompt_title_changed)
        #
        #
        #
        layout.addWidget(self.prompt_title)
        self.instructions = QPlainTextEdit(self)
        self.instructions.setPlaceholderText("Enter your question or any instructions…")
        layout.addWidget(self.instructions)
        #
        # document context checkbox controls doc path visibility
        #
        self.use_doc_checkbox = QCheckBox("Include test-data as context", self)
        self.use_doc_checkbox.setObjectName("utd")
        self.use_doc_checkbox.setChecked(False)
        self.use_doc_checkbox.setStyleSheet("QCheckBox#utd {margin-left:4px}")
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
        #
        # if we are generating data we need to know how many lines to generate.
        # the combo will only show when the clickbox is not showing.
        #
        self.lines_count = QComboBox()
        self.lines_count.addItem("25")
        self.lines_count.addItem("100")
        self.lines_count.addItem("250")
        self.lines = QWidget()
        lines_form = QFormLayout()
        lines_form.setContentsMargins(0, 0, 0, 0)
        lines_form.addRow("Lines", self.lines_count)
        self.lines.setLayout(lines_form)
        layout.addWidget(self.lines)
        self.lines.setVisible(False)
        #
        #
        #
        self.submit_btn = QPushButton("Submit", self)
        box = HelpIconPackager.add_help(
            main=self.main, widget=self.submit_btn, on_help=self.on_ai_help
        )
        box.setMinimumWidth(150)
        box.setStyleSheet(
            "QWidget { margin-bottom:9px; height:25px; padding-right:4px;} "
        )
        layout.addWidget(box)
        #
        # signals
        #
        self.submit_btn.clicked.connect(self._on_submit)
        self.use_doc_checkbox.stateChanged.connect(self.on_use_doc)

        self.max_data_input_lines = 25
        self.max_data_output_lines = 25
        self._current_activity = "validation"
        self.activity_selector.activityChanged.connect(self._on_activity_changed)
        self.submit_btn.setEnabled(False)

    def on_prompt_title_changed(self) -> None:
        t = self.prompt_title.text()
        if t is not None and str(t).strip() != "":
            self.submit_btn.setEnabled(True)
            self.submit_btn.setText("Submit")
        else:
            self.submit_btn.setEnabled(False)
            if self.activity_selector.activity == "question":
                self.submit_btn.setText("Name your question to continue")
            else:
                self.submit_btn.setText("Name your request to continue")

    def assure_state(self) -> None:
        doc = self.main.current_doc_tab
        if doc is None:
            return
        path = doc.objectName()
        print(f"queryform: assure_state: doc: {doc}, path: {path}")
        fs = fiut.split_filename(path)
        if fs[1] in self.main.csvpath_config.get(
            section="extensions", name="csv_files"
        ):
            self.activity_selector.set_activity("validation")
        else:
            self._on_activity_changed(self.activity_selector.activity)
        self.on_prompt_title_changed()

    def on_ai_help(self) -> None:
        md = HelpFinder(main=self.main).help("ai/help.md")
        self.main.helper.get_help_tab().setMarkdown(md)
        if not self.main.helper.is_showing_help():
            self.main.helper.on_click_help()

    def _on_activity_changed(self, mode: str):
        self._current_activity = mode
        if mode == "question":
            self.instructions.setPlaceholderText("Ask your question…")
            self.prompt_title.setPlaceholderText("Name your question…")
        elif mode in ["validation", "explain"]:
            self.instructions.setPlaceholderText("Enter any instructions…")
            self.prompt_title.setPlaceholderText("Name your request…")
        else:
            self.instructions.setPlaceholderText(
                "Any instructions for data generation…"
            )
            self.prompt_title.setPlaceholderText("Name your request…")
        if mode in ["testdata", "validation"]:
            self.doc_path.hide()
            self.use_doc_checkbox.hide()
        else:
            self.use_doc_checkbox.show()
            self.on_use_doc(self.use_doc_checkbox.isChecked())

        self.lines.setVisible(mode == "testdata")

        self.instructions.viewport().update()
        #
        # TODO: show/hide fields depending on mode
        #

    def on_use_doc(self, state: int) -> None:
        if state == Qt.CheckState.Checked.value:
            self.doc_path.show()
            #
            # find the test data, if any
            # TODO: prefer to use the name of the currently viewable tab, rather
            # than selected file path. shouldn't make much difference in practice.
            #
            path = tdut.get_test_data_path(self.main.selected_file_path)
            if path is not None:
                self.doc_path_text.setText(path)
        else:
            self.doc_path.hide()

    #
    # better to use tdut.get_test_data_path
    #
    def _get_test_data_path_if(self) -> str:
        t = self.main.current_doc_tab
        if t is not None:
            _ = t.objectName()
            return tdut.get_test_data_path(_)
            """
            exts = self.main.csvpath_config.get(section="extensions", name="csvpath_files")
            if fiut.is_a(_, exts) and isinstance(t, CsvpathViewer):
                text = t.text_edit.toPlainText()
                s,c = csut.statement_and_comment(text)
                docpath = csut.get_filepath(c)
                return docpath
            """
        return None

    def _on_submit(self):
        #
        # the activity is always w/re: the open document. in the case of question or explaination,
        # it may be useful to look for a test-data: pointer to find a data context. "validation"
        # "testdata" activities don't use this optional capability. it has to be optional because
        # we would be shipping data to the AI API.
        #
        docpath = None
        use_doc_path = self._current_activity in ["question", "explain"] and (
            self.use_doc_checkbox.isChecked()
            and str(self.doc_path_text.text()).strip() != ""
        )
        tdata = None
        if use_doc_path is True:
            docpath = self._get_test_data_path_if()
            tdata = self.get_data_context_from_path_if(docpath)
        #
        #
        #
        title = None
        title = self.prompt_title.text()
        if title is None or str(title).strip() == "":
            title = f"{self._current_activity} {len(self.my_parent.accordion.items)}"
        #
        #
        #
        config = geut.new_generator_config(self.main)
        turns_limit = config.get(section="generations", name="turns_limit", default="8")
        #
        # this is the only place params should be created/added.
        #
        params = {
            "activity": self._current_activity,
            "title": title,
            #
            # instructions == the narrative box for Q&A or instructions for how to generate
            # data, schema, or explain
            #
            "instructions": self.instructions.toPlainText(),
            #
            # example == the main document we're giving to the AI to explain, Q&A, generate
            # schema for, or generate data for example is the Prompt.example.
            #
            "example": self.get_example_content(),
            "example_path": self.get_example_path(),
            #
            # test_data == file contents at docpath, where docpath is a test-data:
            # directive. at this time, we aren't passing the actual data to the AI, only the
            # path. however, capturing an actual sample is potentially useful for future ref.
            #
            "test_data": tdata,
            #
            # data example is a sample that we would pull from the first test-data: metadata
            # token we find, if any. if found, it would be added to the prompt as an extra
            # piece of content in some way appended.
            #
            "test_data_path": docpath,
            #
            # not all activities use these input/output limits, but we need them in some
            # cases and always providing them doesn't hurt.
            #
            "data_input_lines": self.max_data_input_lines,
            "data_output_lines": self.max_data_output_lines,
            #
            # we need to tell the AI how many turns it has so it can wrap up and answer
            # in a timely way
            #
            "turns_limit": int(turns_limit),
        }
        self.querySubmitted.emit(params)

    def load_params(self, params: dict):
        #
        # when an item is clicked, load up the params, form, etc. to get the as-was state for the query
        #
        self.activity_selector.set_activity(params.get("activity", "validation"))
        self.prompt_title.setText(params.get("title", ""))
        self.instructions.setPlainText(params.get("instructions", ""))
        self.use_doc_checkbox.setChecked(bool(params.get("test_data_path")))
        self.set_document_context(params.get("test_data_path"))
        #
        # we want to display any feedback we collected in the help & feedback tabs
        # but we'll do that from the query tab where we caught the event.
        #

    def get_example_path(self) -> str:
        t = self.main.current_doc_tab
        path = t.objectName()
        return path

    def get_example_content(self) -> str:
        if self._current_activity == "validation":
            ret = None
            path = self.get_example_path()
            if path is None:
                raise ValueError("No selected file available")
            with DataFileReader(path) as file:
                #
                # we only give a sample of the data for the AI to consider. atm,
                # hardcoded to 25 lines, but will become more dynamic asap.
                #
                lst = []
                for i, _ in enumerate(file.source):
                    lst.append(_)
                    if i > self.max_data_input_lines:
                        break
                ret = "\n".join(lst)
            return ret
        t = self.main.current_doc_tab
        if isinstance(t, CsvpathViewer):
            #
            # for all the activities where the primary material is a csvpath
            # we want to provide the complete file. in the future maybe we'da
            # want to be able to just offer a subset of the csvpaths in one
            # file, but atm that's not worth doing.
            #
            return t.text_edit.toPlainText()
        raise ValueError(
            f"Activity must be validate ({self._current_activity}) or document {t} must be csvpaths"
        )

    def get_data_context_from_path_if(self, path: str) -> str:
        if path is None:
            return ""
        with DataFileReader(path) as file:
            lst = []
            for i, _ in enumerate(file.source):
                lst.append(_)
                if i > self.max_data_input_lines:
                    break
            ret = "\n".join(lst)
            if ret is not None:
                ret = f"\n\nThis is a sample of my data:\n{ret}"
            return ret

    def set_document_context(self, path: str | None):
        if path:
            self.doc_path_text.setText(path)
            self.doc_path.show()
        else:
            self.doc_path.hide()
