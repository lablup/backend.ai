import time
from abc import ABC, abstractmethod
from typing import Optional


class TestExporter(ABC):
    @classmethod
    @abstractmethod
    async def create(cls, sub_name: Optional[str]) -> "TestExporter":
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
    _sub_name: Optional[str]
    _started: float
    _last_stage_done: float

    def __init__(self, sub_name: Optional[str], started: float, last_stage_done: float) -> None:
        self._sub_name = sub_name
        self._started = started
        self._last_stage_done = last_stage_done

    @classmethod
    async def create(cls, sub_name: Optional[str] = None) -> TestExporter:
        return cls(sub_name, started=0.0, last_stage_done=0.0)

    async def export_start(self, spec_name: str) -> None:
        current = time.perf_counter()
        self._started = current
        self._last_stage_done = current
        print(f"Starting test '{self._spec_name(spec_name)}'...")

    async def export_done(self, spec_name: str) -> None:
        current = time.perf_counter()
        elapsed = current - self._started
        print(f"Test '{self._spec_name(spec_name)}' completed in {elapsed:.2f} seconds.")

    async def export_stage_done(self, stage: str) -> None:
        current = time.perf_counter()
        elapsed = current - self._last_stage_done
        self._last_stage_done = current
        print(f"Stage '{stage}' completed in {elapsed:.2f} seconds.")

    async def export_stage_exception(self, stage: str, exception: BaseException) -> None:
        current = time.perf_counter()
        elapsed = current - self._last_stage_done
        self._last_stage_done = current
        print(
            f"Stage '{stage}' failed after {elapsed:.2f} seconds. {exception.__class__.__name__}: {exception}"
        )

    async def export_exception(self, spec_name: str, exception: BaseException) -> None:
        current = time.perf_counter()
        elapsed = current - self._started
        print(
            f"Test '{self._spec_name(spec_name)}' failed after {elapsed:.2f} seconds. {exception.__class__.__name__}: {exception}"
        )

    def _spec_name(self, spec_name: str) -> str:
        """
        Helper method to format the spec name for export.
        This can be overridden in subclasses for custom formatting.
        """
        if not self._sub_name:
            return spec_name
        return f"{spec_name} ({self._sub_name})"
