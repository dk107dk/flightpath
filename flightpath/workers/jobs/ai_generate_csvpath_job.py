from flightpath.workers.jobs.ai_job import AiJob


class AiGenerateCsvpathJob(AiJob):
    def __init__(self, *, parent, main, mdata: dict):
        super().__init__(main=main, parent=parent, mdata=mdata)

    @property
    def example(self) -> None:
        if self.path is None:
            return ""
        lines = []
        with open(self.path, "r") as file:
            for i, line in enumerate(file):
                lines.append(line)
                #
                # we don't have a chosen number of lines yet
                #
                if i > 20:
                    break
        return "\n".join(lines)

    @property
    def version(self) -> str:
        return "validation"
