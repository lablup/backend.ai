from abc import ABC

from ..testcases.testcases import TestSpec


class TestExporter(ABC):
    async def export_done(self, spec: TestSpec) -> None:
        """
        Export the result of a test run.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    async def export_exception(self, spec: TestSpec, exception: BaseException) -> None:
        """
        Export the exception that occurred during the test run.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class PrintExporter(TestExporter):
    async def export_done(self, spec: TestSpec) -> None:
        print(f"Test '{spec.name()}' completed successfully.")

    async def export_exception(self, spec: TestSpec, exception: BaseException) -> None:
        print(f"Test '{spec.name()}' failed with exception: {exception}")
