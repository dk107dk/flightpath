from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit
from PySide6.QtGui import QColor
from PySide6.QtCore import QThreadPool

from flightpath.widgets.ai.query_form import QueryFormWidget
from flightpath.widgets.ai.query_accordion import QueryAccordionWidget
from flightpath.workers.ai_generate_csvpath_worker import AiGenerateCsvpathWorker
from flightpath.workers.dispatcher import JobDispatcher
from flightpath.workers.jobs.ai_generate_csvpath_job import AiGenerateCsvpathJob
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


    def on_query_submitted(self, params):
        metadata = {
            "id": id(params),
            "params": params,
            "activity": params["activity"],
            "status": "running",
            "document_path": params.get("document_path"),
            "results": None,
        }

        item = self.accordion.add_item(
            title=params.get("title", "Untitled Query"),
            activity=params["activity"],
            status_color=QColor("#ffd43b"),
            metadata=metadata,
        )
        worker = JobDispatcher.get_worker(main=self.main, me=self, mdata=metadata)
        #
        # connect signals. all dispatched ai workers need to support the same.
        #
        worker.signals.turn.connect(lambda js: self.on_turn_update(item, js))
        worker.signals.finished.connect(lambda text: self.on_worker_finished(item, metadata, text))
        worker.signals.error.connect(lambda msg: self.on_worker_error(item, metadata, msg))

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

    def on_worker_finished(self, item, metadata, text):
        metadata["results"] = text
        metadata["status"] = "complete"
        item.status_dot.setColor(QColor("#40c057"))  # green
        #item.title_label.setText("Complete")

    def on_worker_error(self, item, metadata, msg):
        metadata["status"] = "error"
        item.status_dot.setColor(QColor("#fa5252"))  # red
        item.title_label.setText("Error")

    #
    # do we want the user to have to click a link within the item, or is it
    # better for the doc to open when the item is selected? with no slider
    # separation between the form and the accordian, I'm thinking it would
    # probably be better to open the docs so that all the information (form +
    # document context) is presented together. we'll see tho.
    #
    def on_item_clicked(self, metadata: dict):
        self.form.load_params(metadata["params"])
        #
        # show any logging. this would be the generation summaries
        #
        if "log" in metadata["params"]:
            js = metadata["params"]["log"]
        else:
            js = "No query logging available"
        feut.clear_feedback(self.main)
        view = QPlainTextEdit()
        view.setPlainText(js)
        view.setReadOnly(True)
        feut.add_feedback_tab(main=self.main, tab_id=metadata["id"], name="Tracking", tab=view)


    def on_item_close_requested(self, metadata: dict):
        self.accordion.remove_item(metadata)
        #
        # can we check for a worker and attempt to stop it?
        #

