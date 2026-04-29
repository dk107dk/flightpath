from flightpath.workers.jobs.ai_job import AiJob


class AiGenerateCsvpathJob(AiJob):
    def __init__(self, *, parent, main, mdata: dict):
        super().__init__(main=main, parent=parent, mdata=mdata)

    @property
    def version(self) -> str:
        return "validation"
