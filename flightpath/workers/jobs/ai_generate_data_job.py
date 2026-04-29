from flightpath.workers.jobs.ai_job import AiJob


class AiGenerateDataJob(AiJob):
    def __init__(self, *, parent, main, mdata: dict):
        super().__init__(parent=parent, main=main, mdata=mdata)

    @property
    def version(self) -> str:
        return "testdata"
