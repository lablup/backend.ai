import time
from abc import ABC, abstractmethod


class TestExporter(ABC):
    @classmethod
    @abstractmethod
    async def create(cls) -> "TestExporter":
        """
        Create an instance of the exporter.
        This method can be overridden to provide custom initialization logic.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    async def export_start(self, spec_name: str) -> None:
        """
        Export the start of a test run.
        This method can be used to log or notify the start of a test case.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    async def export_done(self, spec_name: str) -> None:
        """
        Export the result of a test run.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    async def export_stage_done(self, stage: str) -> None:
        """
        Export the completion of a stage in the test run.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    async def export_stage_exception(self, stage: str, exception: BaseException) -> None:
        """
        Export the exception that occurred during a stage in the test run.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    async def export_exception(self, spec_name: str, exception: BaseException) -> None:
        """
        Export the exception that occurred during the test run.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class PrintExporter(TestExporter):
    started: float
    last_stage_done: float

    def __init__(self, started: float, last_stage_done: float) -> None:
        self.started = started
        self.last_stage_done = last_stage_done

    @classmethod
    async def create(cls) -> TestExporter:
        return cls(started=0.0, last_stage_done=0.0)

    async def export_start(self, spec_name: str) -> None:
        current = time.perf_counter()
        self.started = current
        self.last_stage_done = current
        print(f"Starting test '{spec_name}'...")

    async def export_done(self, spec_name: str) -> None:
        current = time.perf_counter()
        elapsed = current - self.started
        print(f"Test '{spec_name}' completed in {elapsed:.2f} seconds.")

    async def export_stage_done(self, stage: str) -> None:
        current = time.perf_counter()
        elapsed = current - self.last_stage_done
        self.last_stage_done = current
        print(f"Stage '{stage}' completed in {elapsed:.2f} seconds.")

    async def export_stage_exception(self, stage: str, exception: BaseException) -> None:
        current = time.perf_counter()
        elapsed = current - self.last_stage_done
        self.last_stage_done = current
        print(
            f"Stage '{stage}' failed after {elapsed:.2f} seconds. {exception.__class__.__name__}: {exception}"
        )

    async def export_exception(self, spec_name: str, exception: BaseException) -> None:
        current = time.perf_counter()
        elapsed = current - self.started
        print(
            f"Test '{spec_name}' failed after {elapsed:.2f} seconds. {exception.__class__.__name__}: {exception}"
        )
