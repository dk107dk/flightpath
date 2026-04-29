from flightpath.workers.jobs.ai_job import AiJob


class AiAskQuestionJob(AiJob):
    def __init__(self, *, parent, main, mdata: dict):
        super().__init__(parent=parent, main=main, mdata=mdata)

    @property
    def example(self) -> None:
        e = self._values.get("example")
        t = self._values.get("test_data")
        if e is None:
            return t
        if t is None:
            return e
        return f"""
{e}

An example of some data that goes with that is:
{t}
        """

    @property
    def version(self) -> str:
        return "question"
