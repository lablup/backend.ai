import asyncio
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, final, override

from ai.backend.client.session import AsyncSession
from ai.backend.test.contexts.api_config import APIConfigContext
from ai.backend.test.contexts.client_session import AsyncSessionContext
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

    @abstractmethod
    @actxmgr  # type: ignore
    async def context(self) -> AsyncIterator[None]:
        """
        Async Context manager for setup and cleanup operations.
        This method should be overridden by subclasses to implement specific setup and cleanup logic.
        """
        raise NotImplementedError("Subclasses must implement this method.")
        yield  # Not used, but required for type checking

    @final
    async def run_test(self, exporter: TestExporter) -> None:
        try:
            # NOTE: self.context() should be an async context manager
            async with self.context():  # type: ignore
                await self._template.run_test(exporter)
                await exporter.export_stage_done(self.name)
        except BaseException as e:
            await exporter.export_stage_exception(self.name, e)
            raise


class SequenceTestTemplate(TestTemplate, ABC):
    def __init__(self, templates: list[TestTemplate]) -> None:
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
        for template in self._templates:
            try:
                await template.run_test(exporter)
                await exporter.export_stage_done(self.name)
            except BaseException as e:
                await exporter.export_stage_exception(self.name, e)
                raise


class AsyncSessionTemplate(WrapperTestTemplate):
    def __init__(self, template: TestTemplate) -> None:
        super().__init__(template)

    @property
    def name(self) -> str:
        return "create_client_session"

    @override
    @actxmgr
    async def context(self) -> AsyncIterator[None]:
        api_config = APIConfigContext.get_current()
        async with AsyncSession(config=api_config) as session:
            with AsyncSessionContext.with_current(session):
                yield
