from abc import ABC, abstractmethod


class Job(ABC):

    def __init__(self, *, main):
        if main is None:
            raise ValueError("Main cannot be None")
        self.main = main

    @abstractmethod
    def example(self) -> None:
        ...

    @abstractmethod
    def version(self) -> str:
        ...

    @abstractmethod
    def do_generate() -> None:
        ...

