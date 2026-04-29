import json
import traceback
import copy

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPlainTextEdit,
    QApplication,
    QSplitter,
    QMessageBox,
)
from PySide6.QtGui import QColor
from PySide6.QtCore import QThreadPool, Qt, Slot

import darkdetect

from flightpath.util.editable import EditStates
from flightpath.widgets.ai.query_form import QueryFormWidget
from flightpath.widgets.accordion.query_accordion import QueryAccordionWidget
from flightpath.widgets.panels.json_viewer import JsonViewer
from flightpath.workers.dispatcher import JobDispatcher
from flightpath.util.feedback_utility import FeedbackUtility as feut
from flightpath.util.tabs_utility import TabsUtility as taut


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
        self.accordion.itemInfoRequested.connect(self.on_item_info_requested)

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
        if params is None:
            raise ValueError("Params cannot be None")
        metadata = {
            "id": id(params),
            "params": params,
            "activity": params["activity"],
            "status": "running",
            "example_path": params.get("example_path"),
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
        if not self._valid_instructions(item, metadata):
            return
        worker = JobDispatcher.get_worker(main=self.main, me=self, mdata=metadata)
        worker.signals.finished.connect(
            lambda generation: self.on_worker_finished(item, metadata, generation)
        )
        worker.signals.turn.connect(lambda js: self.on_turn_update(item, js))
        worker.signals.error.connect(
            lambda msg: self.on_worker_error(item, metadata, msg)
        )
        self._dump_job_params(metadata)
        item.worker = worker
        self.threadpool.start(worker)

    def _valid_instructions(self, item, metadata: dict) -> bool:
        params = metadata.get("params")
        instructions = params.get("instructions")
        if self.form._current_activity == "question" and str(instructions).strip() in [
            "None",
            "",
        ]:
            self.on_worker_error(
                item,
                params,
                "You must provide a question or constrant for the AI to help with.",
            )
            return False
        return True

    def _dump_job_params(self, metadata) -> None:
        _ = json.dumps(metadata, indent=2)
        print(f"\nquery_tab: dump_job_params: \n{_}\n")

    def on_turn_update(self, item, js):
        if item:
            item.status_dot.setColor(QColor("#ffd43b"))  # yellow
        if js:
            item.metadata["params"]["log"] = js
            self._display_tracking(item.metadata)
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
        _ = metadata.get("status")
        _ = str(_).strip()
        if _ != "error":
            metadata["status"] = "complete"
            item.status_dot.setColor(QColor("#40c057"))  # green
        else:
            print(
                "qtab: onworkerfinished: item is in error so not setting it to complete/green"
            )
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
        print(f"query acc item: metadata: {len(metadata)}")
        print(f"                item: {item}")
        print(f"                msg: {msg}")
        for k, v in metadata.items():
            if k == "params":
                print(f"               ...{k}:")
                for i, j in v.items():
                    print(f"                   ....{i} = {j}")
            else:
                print(f"               ...{k} = {v}")

        metadata["status"] = "error"
        metadata["error"] = msg
        item.status_dot.setColor(QColor("#fa5252"))  # red
        item.subtitle.setText("Error")
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
        # update/show the tracking
        #
        self._display_tracking(item.metadata)
        #
        # display feedback
        #
        feut.switch_to_feedback(self.main, error)
        feut.open_feedback_if(self.main)

    @Slot(int)
    def _open_ai_config(self, doit: int) -> None:
        if doit == QMessageBox.Yes:
            self.main.open_ai_config()
            return

    def on_item_info_requested(self, metadata: dict) -> None: ...

    def _display_tracking(self, metadata: dict) -> None:
        tracking = f"{metadata['id']}.tracking"
        t = taut.find_tab(self.main.helper.help_and_feedback, tracking)
        if t is None:
            ...
        else:
            self.main.helper.help_and_feedback.removeTab(t[0])
        view = None
        if "log" in metadata["params"]:
            js = metadata["params"]["log"]
            js = json.loads(js)
            view = JsonViewer.temp_file_viewer(
                main=self.main, parent=self, js=js, can_always_save=True
            )
            view.path = tracking
        else:
            js = "No tracking available"
            view = QPlainTextEdit()
            view.setPlainText(js)
            view.setReadOnly(True)
        view.setObjectName(tracking)
        feut.add_feedback_tab(
            main=self.main, tab_id=tracking, name="Tracking", tab=view
        )

    def _display_job_params(self, metadata: dict) -> None:
        results = metadata.get("results")
        if results:
            del metadata["results"]
        try:
            mdata = copy.deepcopy(metadata)
            params = mdata.get("params")
            if "log" in params:
                del params["log"]

            name = f"{mdata['id']}.params"
            t = taut.find_tab(self.main.helper.help_and_feedback, name)
            if t is None:
                ...
            else:
                self.main.helper.help_and_feedback.removeTab(t[0])
            view = JsonViewer.temp_file_viewer(
                main=self.main, parent=self, js=mdata, can_always_save=True
            )
            view.setObjectName(name)
            feut.add_feedback_tab(
                main=self.main, tab_id=name, name="Request Info", tab=view
            )
        finally:
            if results:
                metadata["results"] = results

    #
    # do we want the user to have to click a link within the item, or is it
    # better for the doc to open when the item is selected? with no slider
    # separation between the form and the accordian, I'm thinking it would
    # probably be better to open the docs so that all the information (form +
    # document context) is presented together. we'll see tho.
    #
    @Slot(dict)
    def on_item_clicked(self, metadata: dict):
        self.form.load_params(metadata["params"])
        feut.clear_feedback(self.main)
        #
        #
        #
        response = f"{metadata['id']}.response"
        tracking = f"{metadata['id']}.tracking"
        instructions = f"{metadata['id']}.instructions"
        error = f"{metadata['id']}.error"
        #
        # show result, if available
        #
        generation = metadata.get("results")
        if generation:
            view = QPlainTextEdit()
            view.setPlainText(generation.response_text)
            view.setReadOnly(True)
            feut.add_feedback_tab(
                main=self.main, tab_id=response, name="Results", tab=view
            )
        else:
            print("qtab: _on_item_clicked: no generation available")
        #
        # show tracking log
        #
        self._display_tracking(metadata)
        #
        #
        #
        self._display_job_params(metadata)
        #
        # show instructions
        #
        inst = metadata.get("params").get("instructions")
        if str(inst).strip() in ["None", ""]:
            inst = "There were no instructions for the AI"
        view = QPlainTextEdit()
        view.setPlainText(inst)
        view.setReadOnly(True)
        view.setObjectName(instructions)
        feut.add_feedback_tab(
            main=self.main, tab_id=instructions, name="Instructions", tab=view
        )
        #
        # show any error
        #
        error_text = metadata.get("error")
        if error_text is None:
            print("qtab: on_item_clicked: no error")
        else:
            view = QPlainTextEdit()
            view.setPlainText(error_text)
            view.setReadOnly(True)
            feut.add_feedback_tab(main=self.main, tab_id=error, name="Error", tab=view)
        #
        # display feedback tabs
        #
        feut.switch_to_feedback(self.main, response if generation else tracking)
        feut.open_feedback_if(self.main)
        #
        # open or switch to the original doc. it is possible the doc could be gone so we'll
        # take a bit more care to not crash. if the doc is not there we don't really care.
        #
        try:
            path = metadata.get("example_path")
            if path is not None:
                editable = self.main.is_doc_editable(path)
                self.main.read_validate_and_display_file_for_path(
                    path,
                    EditStates.EDITABLE if editable is True else EditStates.UNEDITABLE,
                )
        except Exception:
            print(traceback.format_exc())

    @Slot(dict)
    def on_item_close_requested(self, metadata: dict):
        self.accordion.remove_item(metadata)
        #
        # can we check for a worker and attempt to stop it?
        #
