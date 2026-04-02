from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPlainTextEdit,
    QApplication,
    QTextEdit,
)
from PySide6.QtGui import QColor
from PySide6.QtCore import QThreadPool


from flightpath.widgets.ai.query_form import QueryFormWidget
from flightpath.widgets.ai.query_accordion import QueryAccordionWidget
from flightpath.workers.dispatcher import JobDispatcher
from flightpath.util.feedback_utility import FeedbackUtility as feut


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

        layout.addWidget(self.form)
        layout.addWidget(self.accordion, 1)

        self.form.querySubmitted.connect(self.on_query_submitted)
        self.accordion.itemClicked.connect(self.on_item_clicked)
        self.accordion.itemCloseRequested.connect(self.on_item_close_requested)

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
        """
        import json
        print(json.dumps(metadata, indent=2))
        """
        #
        # get this from a user-driven form control?
        #
        activity = self.form.activity_selector.activity
        item = self.accordion.add_item(
            title=params.get("title", "Untitled Query"),
            activity=activity,
            status_color=QColor("#ffd43b"),
            metadata=metadata,
        )
        instructions = metadata.get("params").get("instructions")
        if (
            self.form._current_activity == "question"
            and str(instructions).strip() == ""
        ):
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

    def on_worker_finished(self, item, metadata, generation):
        if generation is None:
            self.on_worker_error(
                item, metadata, "Invalid result metadata: no generation"
            )
            return
        if generation.errors is not None:
            self.on_worker_error(item, metadata, generation.errors)
            return
        if generation.generator.exceptions and len(generation.generator.exceptions) > 0:
            errors = ""
            for _ in generation.generator.exceptions:
                errors = f"{errors}\n{_}"
            self.on_worker_error(item, metadata, errors)
            return
        print(f"querytab.on_worker_finished: {item}, {metadata}, {generation}")
        metadata["results"] = generation
        metadata["status"] = "complete"
        item.status_dot.setColor(QColor("#40c057"))  # green
        self._beep()
        item.worker = None

    def _beep(self) -> None:
        try:
            QApplication.beep()
        except Exception:
            print("beep error")
            ...

    def on_worker_error(self, item, metadata, msg):
        metadata["status"] = "error"
        item.status_dot.setColor(QColor("#fa5252"))  # red
        QApplication.beep()
        item.title_label.setText("Error")
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
            print("on_item_clicked: no generation available from metadata")
        #
        # log info
        #
        if "log" in metadata["params"]:
            js = metadata["params"]["log"]
        else:
            js = "No tracking available"
        view = QPlainTextEdit()
        view.setPlainText(js)
        view.setReadOnly(True)
        feut.add_feedback_tab(
            main=self.main, tab_id=tracking, name="Tracking", tab=view
        )
        #
        # display feedback
        #
        feut.switch_to_feedback(self.main, response if generation else tracking)
        feut.open_feedback(self.main)

    def on_item_close_requested(self, metadata: dict):
        self.accordion.remove_item(metadata)
        #
        # can we check for a worker and attempt to stop it?
        #
