from flightpath.workers.jobs.ai_job import AiJob

class AiExplainJob(AiJob):

    def __init__(self, *, parent, main, mdata:dict):
        super().__init__(parent=parent, main=main, mdata=mdata)
        print("AiExplainJob: getting an explanation")

    @property
    def example(self) -> None:
        if self.path is None:
            return ""
        lines = []
        with open(self.path, "r") as file:
            return file.read()

    @property
    def version(self) -> str:
        return "explain"



