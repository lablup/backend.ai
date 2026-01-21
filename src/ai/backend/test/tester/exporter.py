import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ai.backend.common.json import pretty_json_str
from ai.backend.test.contexts.tester import TestSpecMetaContext


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
    async def export_start(self) -> None:
        """
        Export the start of a test run.
        This method can be used to log or notify the start of a test case.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    async def export_done(self) -> None:
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
    async def export_exception(self, exception: BaseException) -> None:
        """
        Export the exception that occurred during the test run.
        """
        raise NotImplementedError("Subclasses must implement this method.")


_DEFAULT_OUTPUT_DIRECTORY = Path("test_output")


@dataclass
class ErrorOutput:
    test_id: str
    spec_name: str
    sub_name: Optional[str]
    stage: str
    exception_name: str
    traceback: str


class DefaultExporter(TestExporter):
    _sub_name: Optional[str]
    _started: float
    _last_stage: Optional[str]
    _last_stage_done: float
    _output_directory: Path

    def __init__(self, sub_name: Optional[str], started: float, last_stage_done: float) -> None:
        self._sub_name = sub_name
        self._started = started
        self._last_stage = None
        self._last_stage_done = last_stage_done
        self._output_directory = _DEFAULT_OUTPUT_DIRECTORY
        if not self._output_directory.exists():
            self._output_directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    async def create(cls, sub_name: Optional[str] = None) -> TestExporter:
        return cls(sub_name, started=0.0, last_stage_done=0.0)

    async def export_start(self) -> None:
        current = time.perf_counter()
        self._started = current
        self._last_stage_done = current
        print(f"Starting '{self._spec_name()}'...")

    async def export_done(self) -> None:
        current = time.perf_counter()
        elapsed = current - self._started
        print(f"\033[92m✓ '{self._spec_name()}' completed in {elapsed:.2f} seconds.\033[0m")

    async def export_stage_done(self, stage: str) -> None:
        current = time.perf_counter()
        elapsed = current - self._last_stage_done
        self._last_stage_done = current
        self._last_stage = stage
        print(f"\033[92m✓ '{self._stage_name(stage)}' completed in {elapsed:.2f} seconds.\033[0m")

    async def export_stage_exception(self, stage: str, exception: BaseException) -> None:
        current = time.perf_counter()
        elapsed = current - self._last_stage_done
        self._last_stage_done = current
        print(
            f"\033[91m❌ '{self._stage_name(stage)}' failed after {elapsed:.2f} seconds. "
            f"{exception.__class__.__name__}\033[0m"
        )

    async def export_exception(self, exception: BaseException) -> None:
        current = time.perf_counter()
        elapsed = current - self._started
        print(
            f"\033[91m❌ '{self._spec_name()}' failed after {elapsed:.2f} seconds. "
            f"{exception.__class__.__name__}\033[0m"
        )
        self._dump_exception(exception)

    def _spec_name(self) -> str:
        """
        Helper method to format the spec name for export.
        This can be overridden in subclasses for custom formatting.
        """
        spec_meta = TestSpecMetaContext.current()
        spec_name = spec_meta.spec_name
        if not self._sub_name:
            return spec_name
        return f"Test {spec_name} ({self._sub_name})"

    def _stage_name(self, stage: str) -> str:
        """
        Helper method to format the stage name for export.
        This can be overridden in subclasses for custom formatting.
        """
        return f"{self._spec_name()} - {stage}"

    def _dump_exception(self, exception: BaseException) -> None:
        """
        Dump the exception to a file in the output directory.
        This can be overridden in subclasses for custom exception handling.
        """
        spec_meta = TestSpecMetaContext.current()
        file_path = self._output_directory / f"{spec_meta.test_id}_exception.log"
        output = ErrorOutput(
            test_id=str(spec_meta.test_id),
            spec_name=spec_meta.spec_name,
            sub_name=self._sub_name,
            stage=self._last_stage or "no stage",
            exception_name=exception.__class__.__name__,
            traceback="".join(
                traceback.format_exception(
                    type(exception), value=exception, tb=exception.__traceback__
                )
            ),
        )
        with file_path.open("w") as f:
            f.write(pretty_json_str(output))

        print(f"Exception details written to {file_path}")
