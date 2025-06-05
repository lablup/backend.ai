from abc import ABC


class TestExporter(ABC):
    async def export_done(self, spec_name: str) -> None:
        """
        Export the result of a test run.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    async def export_stage_done(self, stage: str) -> None:
        """
        Export the completion of a stage in the test run.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    async def export_stage_exception(self, stage: str, exception: BaseException) -> None:
        """
        Export the exception that occurred during a stage in the test run.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    async def export_exception(self, spec_name: str, exception: BaseException) -> None:
        """
        Export the exception that occurred during the test run.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class PrintExporter(TestExporter):
    async def export_done(self, spec_name: str) -> None:
        print(f"Test '{spec_name}' completed successfully.")

    async def export_stage_done(self, stage: str) -> None:
        print(f"Stage '{stage}' completed successfully.")

    async def export_stage_exception(self, stage: str, exception: BaseException) -> None:
        print(f"Stage '{stage}' failed with exception: {exception}")

    async def export_exception(self, spec_name: str, exception: BaseException) -> None:
        print(f"Test '{spec_name}' failed with exception: {exception}")
