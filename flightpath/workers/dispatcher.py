from PySide6.QtCore import QRunnable

from flightpath.workers.jobs.ai_generate_csvpath_job import AiGenerateCsvpathJob
from flightpath.workers.ai_generate_csvpath_worker import AiGenerateCsvpathWorker
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
        if activity == "improve":
            return cls.improve(main=main, me=me, mdata=mdata)
        raise ValueError(f"Unknown activity: {activity}")

    @classmethod
    def validation(cls, *, me, main, mdata:dict) -> Job:
        job = AiGenerateCsvpathJob(
            parent=me,
            main=main,
            mdata=mdata
        )
        w =  AiGenerateCsvpathWorker(job)
        return w

    @classmethod
    def testdata(cls, *, me, main, mdata:dict) -> Job:
        """
        job = AiGenerateCsvJob(
            parent=me,
            main=main,
            path=mdata.get("params", {}).params.get("document_path"),
            instructions=mdata.get("params", {}).params.get("body")
        )
        w =  AiGenerateCsvWorker(job)
        return w
        """

    @classmethod
    def question(cls, *, me, main, mdata:dict) -> Job:
        """
        job = AiQuestionCsvpathJob(
            parent=me,
            main=main,
            path=mdata.get("params", {}).params.get("document_path"),
            instructions=mdata.get("params", {}).params.get("body")
        )
        w =  AiQuestionCsvpathWorker(job)
        return w
        """

    @classmethod
    def improve(cls, *, me, main, mdata:dict) -> Job:
        raise Exception("not implemented")


