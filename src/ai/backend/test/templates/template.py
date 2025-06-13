from abc import ABC, abstractmethod
from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, Protocol, final

from ai.backend.test.tester.exporter import TestExporter


class WrapperTestTemplateProtocol(Protocol):
    @classmethod
    def wrap(cls, template: "TestTemplate") -> "TestTemplate":
        """
        Class method to wrap a test template with a wrapper template.
        :param template: The test template to wrap.
        """
        raise NotImplementedError("Subclasses must implement this method.")


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
        return


class TestTemplate(ABC):
    @final
    def with_wrappers(self, *wrappers: WrapperTestTemplateProtocol) -> "TestTemplate":
        """
        Create a wrapper test template with the given template and optional wrapper templates.
        This method is syntactic sugar for wrapping the current template
        with the provided wrapper templates in reverse order.
        """
        current = self
        for wrapper in wrappers[::-1]:
            current = wrapper.wrap(current)
        return current

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


@final
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

    @final
    @classmethod
    def wrap(cls, template: "TestTemplate") -> "TestTemplate":
        """
        Class method to wrap a test template with this wrapper template.
        :param template: The test template to wrap.
        :return: An instance of the test template.
        """
        return cls(template)

    @abstractmethod
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        """
        Async Context manager for setup and cleanup operations.
        This method should be overridden by subclasses to implement specific setup and cleanup logic.
        """
        raise NotImplementedError("Subclasses must implement this method.")
        yield  # Not used, but required for type checking (mypy issue)

    @final
    async def run_test(self, exporter: TestExporter) -> None:
        try:
            async with self._context():
                await exporter.export_stage_done(self.name)
                await self._template.run_test(exporter)
        except BaseException as e:
            await exporter.export_stage_exception(self.name, e)
            raise


class SequenceTestTemplate(TestTemplate, ABC):
    def __init__(
        self,
        templates: list[TestTemplate],
    ) -> None:
        """
        Initialize the sequence template with a list of test templates.

        :param templates: The list of test templates to run in sequence.
        """
        self._templates = templates

    @final
    async def run_test(self, exporter: TestExporter) -> None:
        """
        Run the test case by executing each template in sequence.
        :param exporter: The exporter to use for exporting test results.
        """
        try:
            for template in self._templates:
                await template.run_test(exporter)
            await exporter.export_stage_done(self.name)
        except BaseException as e:
            await exporter.export_stage_exception(self.name, e)
            raise
