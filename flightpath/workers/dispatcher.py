from PySide6.QtCore import QRunnable

from flightpath.workers.jobs.ai_generate_csvpath_job import AiGenerateCsvpathJob
from flightpath.workers.jobs.ai_generate_data_job import AiGenerateDataJob
from flightpath.workers.jobs.ai_ask_question_job import AiAskQuestionJob
from flightpath.workers.jobs.ai_explain_job import AiExplainJob

from flightpath.workers.ai_worker import AiWorker

from flightpath.workers.jobs.job import Job

class JobDispatcher:

    @classmethod
    def get_worker(cls, main, me, mdata:dict) -> QRunnable:
        if mdata is None:
            raise ValueError("Metadata cannot be None")
        params = mdata.get("params", {})
        activity = params.get("activity")
        if activity is None:
            raise ValueError("Activity cannot be None")
        if activity == "validation":
            return cls.validation(main=main, me=me, mdata=mdata)
        if activity == "testdata":
            return cls.testdata(main=main, me=me, mdata=mdata)
        if activity == "question":
            return cls.question(main=main, me=me, mdata=mdata)
        if activity == "explain":
            return cls.explain(main=main, me=me, mdata=mdata)
        raise ValueError(f"Unknown activity: {activity}")

    @classmethod
    def validation(cls, *, me, main, mdata:dict) -> Job:
        job = AiGenerateCsvpathJob(
            parent=me,
            main=main,
            mdata=mdata
        )
        w =  AiWorker(job)
        return w

    @classmethod
    def testdata(cls, *, me, main, mdata:dict) -> Job:
        job = AiGenerateDataJob(
            parent=me,
            main=main,
            mdata=mdata
        )
        w =  AiWorker(job)
        return w

    @classmethod
    def question(cls, *, me, main, mdata:dict) -> Job:
        job = AiAskQuestionJob(
            parent=me,
            main=main,
            mdata=mdata
        )
        w =  AiWorker(job)
        return w

    @classmethod
    def explain(cls, *, me, main, mdata:dict) -> Job:
        job = AiExplainJob(
            parent=me,
            main=main,
            mdata=mdata
        )
        w =  AiWorker(job)
        return w


