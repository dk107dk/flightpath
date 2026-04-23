import json
import tempfile
import traceback

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPlainTextEdit,
    QApplication,
    QSplitter,
    QTextEdit,
    QMessageBox,
)
from PySide6.QtGui import QColor
from PySide6.QtCore import QThreadPool, Qt

import darkdetect

from flightpath.util.editable import EditStates
from flightpath.widgets.ai.query_form import QueryFormWidget
from flightpath.widgets.accordion.query_accordion import QueryAccordionWidget
from flightpath.widgets.panels.json_viewer import JsonViewer
from flightpath.workers.dispatcher import JobDispatcher
from flightpath.util.feedback_utility import FeedbackUtility as feut
from flightpath.util.message_utility import MessageUtility as meut


class QueryTabWidget(QWidget):
    def __init__(self, *, parent=None, main):
        super().__init__(parent)
        self.main = main
        self.threadpool = QThreadPool.globalInstance()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.form = QueryFormWidget(parent=self, main=main)
        self.accordion = QueryAccordionWidget(self)
        #
        # setup splitter here
        #
        self.ai_split = QSplitter(Qt.Vertical)
        layout.addWidget(self.ai_split)
        self.ai_split.addWidget(self.form)
        self.ai_split.addWidget(self.accordion)
        self.ai_split.setSizes([100, 300])

        self.form.querySubmitted.connect(self.on_query_submitted)
        self.accordion.itemClicked.connect(self.on_item_clicked)
        self.accordion.itemCloseRequested.connect(self.on_item_close_requested)

    def update_style(self) -> None:
        if darkdetect.isDark():
            ...
        else:
            ...
        self.accordion.update_style()

    def enable_for_extension(self, e: str) -> None:
        self.form.activity_selector.enable_for_extension(e)
        #
        # we need the doc checkbox only if "question" or "explain", not "testdata" or "validate"
        # this isn't there yet
        #
        if e in self.main.csvpath_config.get(
            section="extensions", name="csvpath_files"
        ):
            self.form.use_doc_checkbox.setChecked(True)
            self.form.use_doc_checkbox.setEnabled(True)
        #
        #
        if e in self.main.csvpath_config.get(
            section="extensions", name="csv_files"
        ) or e in self.main.csvpath_config.get(
            section="extensions", name="csvpath_files"
        ):
            self.form.prompt_title.setEnabled(True)
            self.form.instructions.setEnabled(True)
            self.form.submit_btn.setEnabled(True)
        else:
            self.form.prompt_title.setEnabled(False)
            self.form.instructions.setEnabled(False)
            self.form.use_doc_checkbox.setChecked(False)
            self.form.use_doc_checkbox.setEnabled(False)
            self.form.submit_btn.setEnabled(False)

    def on_query_submitted(self, params):
        metadata = {
            "id": id(params),
            "params": params,
            "activity": params["activity"],
            "status": "running",
            "document_path": params.get("document_path"),
            "results": None,
            "turns_limit": params.get("turns_limit"),
        }
        #
        # get this from a user-driven form control?
        #
        activity = self.form.activity_selector.activity
        subtitle = ""
        if activity in self.form.activity_selector.SUBTITLES_INITIAL:
            subtitle = self.form.activity_selector.SUBTITLES_INITIAL[activity]
        item = self.accordion.add_item(
            title=params.get("title", "Untitled Query"),
            activity=activity,
            status_color=QColor("#ffd43b"),
            metadata=metadata,
            subtitle=subtitle,
        )

        instructions = metadata.get("params").get("instructions")
        if self.form._current_activity == "question" and str(instructions).strip() in [
            "None",
            "",
        ]:
            self.on_worker_error(
                item,
                metadata,
                "You must provide a question or constrant for the AI to help with.",
            )
            return
        worker = JobDispatcher.get_worker(main=self.main, me=self, mdata=metadata)
        worker.signals.finished.connect(
            lambda generation: self.on_worker_finished(item, metadata, generation)
        )
        worker.signals.turn.connect(lambda js: self.on_turn_update(item, js))
        worker.signals.error.connect(
            lambda msg: self.on_worker_error(item, metadata, msg)
        )
        item.worker = worker
        self.threadpool.start(worker)

    def on_turn_update(self, item, js):
        if item:
            item.status_dot.setColor(QColor("#ffd43b"))  # yellow
        if js:
            item.metadata["params"]["log"] = js
            #
            # do we want to clear? we don't want to do it here because the user may have been
            # working on something.
            #
            self.update_subtitle(item)

    def update_subtitle(self, item) -> str:
        n = None
        if item and item.worker and item.worker.job and item.worker.job.generator:
            n = item.worker.job.generator.turn_number
            n = n + 1
        if n is None:
            return
        t = item.subtitle.text()
        if t.strip().endswith("."):
            t = t[0 : t.find(".")]
        t = f"{t}. Turn {n}."
        item.subtitle.setText(t)

    def on_worker_finished(self, item, metadata, generation):
        if generation is None:
            self.on_worker_error(
                item, metadata, "Invalid result metadata: no generation"
            )
            return
        if generation.errors is not None:
            print(f"querytab: error 1: {generation.errors}")
            self.on_worker_error(item, metadata, generation.errors)
            return
        if generation.generator.exceptions and len(generation.generator.exceptions) > 0:
            print(f"querytab: error 2: {generation.generator.exceptions}")
            errors = ""
            for _ in generation.generator.exceptions:
                errors = f"{errors}\n{_}"
            self.on_worker_error(item, metadata, errors)
            return
        metadata["results"] = generation
        metadata["status"] = "complete"
        item.status_dot.setColor(QColor("#40c057"))  # green
        self._beep()
        item.worker = None

    def _beep(self) -> None:
        try:
            QApplication.beep()
        except Exception:
            ...

    #
    # {'activity': 'validation',
    #  'data_example': '',
    #  'data_input_lines': 25,
    #  'data_output_lines': 25,
    #  'document_path': None,
    #  'example': '...'
    #  'instructions': '',
    #  'number_of_lines': '25',
    #  'title': 'health',
    #  'turns_limit': '15',
    #  'use_document': False
    # },
    # 'activity': 'validation',
    # 'status': 'running',
    # 'document_path': None,
    # 'results': None,
    # 'turns_limit': '15'},
    #
    # item: <flightpath.widgets.ai.query_accordion_item.QueryAccordionItem(0x17fc53af0) at 0x15e9f7e00>,
    # msg: litellm.RateLimitError: RateLimitError: OpenAIException - Request too large for gpt-4o-mini in organization org-IMB8R5BT37cEOcGYZ04vJaxY on tokens per min (TPM): Limit 200000, Requested 523138. The input or output tokens must be reduced in order to run successfully. Visit https://platform.openai.com/account/rate-limits to learn more.
    #
    def on_worker_error(self, item, metadata, msg):
        print(f"query acc item: metadata: {metadata}, item: {item}, msg: {msg}")
        metadata["status"] = "error"
        metadata["error"] = msg
        item.status_dot.setColor(QColor("#fa5252"))  # red
        item.subtitle.setText("Error")
        QApplication.beep()
        # item.title.setText("Error")
        self._beep()
        #
        # put the error in the Tracking tab
        #
        view = QPlainTextEdit()
        view.setPlainText(msg)
        view.setReadOnly(True)
        error = f"{metadata['id']}.error"
        feut.add_feedback_tab(main=self.main, tab_id=error, name="Error", tab=view)
        #
        # display feedback
        #
        feut.switch_to_feedback(self.main, error)
        feut.open_feedback(self.main)

    #
    # do we want the user to have to click a link within the item, or is it
    # better for the doc to open when the item is selected? with no slider
    # separation between the form and the accordian, I'm thinking it would
    # probably be better to open the docs so that all the information (form +
    # document context) is presented together. we'll see tho.
    #
    def on_item_clicked(self, metadata: dict):
        print(f"quertab: on_item_clicked: metadata: {metadata}")
        self.form.load_params(metadata["params"])
        feut.clear_feedback(self.main)
        #
        # show result text
        #
        response = f"{metadata['id']}.response"
        generation = metadata.get("results")
        tracking = f"{metadata['id']}.tracking"
        #
        if generation:
            view = QTextEdit()
            view.setMarkdown(generation.response_text)
            view.setReadOnly(True)
            feut.add_feedback_tab(
                main=self.main, tab_id=response, name="Results", tab=view
            )
        else:
            if self.main and self.main.csvpath_config:
                if self.main.csvpath_config.get(section="llm", name="model") is None:
                    o = meut.yesNoButtons(
                        parent=self,
                        title="Assistance Failed",
                        msg="Request did not complete. Open AI configuration?",
                        std_buttons=QMessageBox.Open | QMessageBox.Cancel,
                        truth_button=QMessageBox.Open,
                        def_button=QMessageBox.Cancel,
                    )
                    if o is True:
                        self.main.open_ai_config()
                        return
                else:
                    meut.warning(
                        parent=self,
                        title="Assistance Failed",
                        msg="Request did not complete.",
                    )
            else:
                meut.warning(
                    parent=self,
                    title="Config Failed",
                    msg="Configuration is unavailable.",
                )
        #
        # show log info
        #
        if "log" in metadata["params"]:
            js = metadata["params"]["log"]

            print(f"\n\nquerytwsb: js: {js}")

            with tempfile.NamedTemporaryFile(
                mode="w", delete=True, suffix=".json"
            ) as file:
                #
                # for the moment, loading js confirms that it is good json. probably not necessary.
                #
                _data = json.loads(js)
                _data = json.dumps(_data, indent=2)
                file.write(_data)
                file.flush()
                view = JsonViewer(
                    parent=self.main.rt_tab_widget,
                    main=self.main,
                    editable=EditStates.UNEDITABLE,
                )
                view.open_file(path=file.name, data=_data)
                view.setObjectName(file.name)
        else:
            js = "No tracking available"
            view = QPlainTextEdit()
            view.setPlainText(js)
            view.setReadOnly(True)

        feut.add_feedback_tab(
            main=self.main, tab_id=tracking, name="Tracking", tab=view
        )

        #
        # show any error
        #
        error = metadata.get("error")
        if error is not None:
            view = QPlainTextEdit()
            view.setPlainText(error)
            view.setReadOnly(True)
            error = f"{metadata['id']}.error"
            feut.add_feedback_tab(main=self.main, tab_id=error, name="Error", tab=view)
        #
        # display feedback
        #
        feut.switch_to_feedback(self.main, response if generation else tracking)
        feut.open_feedback(self.main)
        #
        # open or switch to the original doc. it is possible the doc could be gone so we'll
        # take a bit more care to not crash. if the doc is not there we don't really care.
        #
        try:
            path = metadata.get("document_path")
            editable = self.main.is_doc_editable(path)
            if path is not None:
                self.main.read_validate_and_display_file_for_path(
                    path,
                    EditStates.EDITABLE if editable is True else EditStates.UNEDITABLE,
                )
        except Exception:
            print(traceback.format_exc())

    def on_item_close_requested(self, metadata: dict):
        self.accordion.remove_item(metadata)
        #
        # can we check for a worker and attempt to stop it?
        #
