import asyncio
from abc import ABC, abstractmethod

from ai.backend.test.tester.exporter import TestExporter


class TestCode(ABC):
    @abstractmethod
    async def test(self) -> None:
        """
        Run the test case. This method should be overridden by subclasses
        to implement the specific test logic.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class NopTestCode(TestCode):
    async def test(self) -> None:
        """
        A no-operation test code that does nothing.
        This can be used as a placeholder for tests that do not require any action.
        """
        await asyncio.sleep(0)  # Simulate a no-op with an async sleep
        return


class TestTemplate(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the name of the test template.
        This method should be overridden by subclasses to provide a specific name.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    async def run_test(self, exporter: TestExporter) -> None:
        """
        Run the test case. This method should be overridden by subclasses
        to implement the specific test logic.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class BasicTestTemplate(TestTemplate):
    _testcode: TestCode

    def __init__(self, testcode: TestCode) -> None:
        """
        Initialize the basic template with a test code function.

        :param testcode: The test code function to run.
        """
        self._testcode = testcode

    @property
    def name(self) -> str:
        return "basic"

    async def run_test(self, exporter: TestExporter) -> None:
        await self._testcode.test()


class WrapperTestTemplate(TestTemplate, ABC):
    _template: TestTemplate

    def __init__(self, template: TestTemplate) -> None:
        """
        Initialize the wrapper template with a test template.

        :param template: The test template to wrap.
        """
        self._template = template

    @abstractmethod
    async def setup(self) -> None:
        """
        Set up the test environment. This method should be overridden by subclasses
        to perform any necessary setup before running the test.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    async def run_test(self, exporter: TestExporter) -> None:
        await self.setup()
        try:
            await self._template.run_test(exporter)
            await exporter.export_stage_done(self.name)
        except BaseException as e:
            await exporter.export_stage_exception(self.name, e)
            raise
        finally:
            await self.cleanup()

    @abstractmethod
    async def cleanup(self) -> None:
        """
        Clean up after the test. This method should be overridden by subclasses
        to perform any necessary cleanup after running the test.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class SequenceTestTemplate(TestTemplate, ABC):
    def __init__(self, templates: list[TestTemplate]) -> None:
        """
        Initialize the sequence template with a list of test templates.
        :param templates: The list of test templates to run in sequence.
        """
        self._templates = templates

    async def run_test(self, exporter: TestExporter) -> None:
        """
        Run the test case by executing each template in sequence.
        :param exporter: The exporter to use for exporting test results.
        """
        for template in self._templates:
            try:
                await template.run_test(exporter)
                await exporter.export_stage_done(self.name)
            except BaseException as e:
                await exporter.export_stage_exception(self.name, e)
                raise
