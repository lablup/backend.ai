from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, Protocol, final

from ai.backend.test.tester.exporter import TestExporter


class WrapperTestTemplateProtocol(Protocol):
    def __call__(
        self, template: "TestTemplate", wrapper_templates: list["WrapperTestTemplateProtocol"] = []
    ) -> "WrapperTestTemplate": ...


@actxmgr
async def _apply_wrapper_templates(
    wrapper_templates: list["WrapperTestTemplateProtocol"], exporter: TestExporter
) -> AsyncIterator[None]:
    async with AsyncExitStack() as stack:
        try:
            stage_name = "undefined"
            for w in wrapper_templates:
                if isinstance(w, WrapperTestTemplate):
                    wrapper = w
                else:
                    empty = BasicTestTemplate(NopTestCode())
                    # TODO: Improve this type hinting
                    wrapper = w(empty, [])  # type: ignore

                stage_name = wrapper.name
                await stack.enter_async_context(wrapper.context())
                await wrapper._template.run_test(exporter)
                await exporter.export_stage_done(stage_name)
            yield
        except BaseException as e:
            await exporter.export_stage_exception(stage_name, e)
            raise


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
    _wrapper_templates: list["WrapperTestTemplateProtocol"]

    def __init__(
        self, testcode: TestCode, wrapper_templates: list["WrapperTestTemplateProtocol"] = []
    ) -> None:
        """
        Initialize the basic template with a test code function.

        :param testcode: The test code function to run.
        :param wrapper_templates: Optional list of wrapper templates to apply before running the test code.
        """
        self._testcode = testcode
        self._wrapper_templates = wrapper_templates

    @property
    def name(self) -> str:
        return "basic"

    async def run_test(self, exporter: TestExporter) -> None:
        async with _apply_wrapper_templates(self._wrapper_templates, exporter):
            try:
                await self._testcode.test()
                await exporter.export_stage_done(self.name)
            except BaseException as e:
                await exporter.export_stage_exception(self.name, e)
                raise


class WrapperTestTemplate(TestTemplate, ABC):
    _template: TestTemplate
    _wrapper_templates: list["WrapperTestTemplateProtocol"]

    def __init__(
        self, template: TestTemplate, wrapper_templates: list["WrapperTestTemplateProtocol"] = []
    ) -> None:
        """
        Initialize the wrapper template with a test template.

        :param template: The test template to wrap.
        :param wrapper_templates: Optional list of additional wrapper templates to apply.
        """
        self._template = template
        self._wrapper_templates = wrapper_templates

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
        async with _apply_wrapper_templates(self._wrapper_templates, exporter):
            try:
                await self._template.run_test(exporter)
                await exporter.export_stage_done(self.name)
            except BaseException as e:
                await exporter.export_stage_exception(self.name, e)
                raise


class SequenceTestTemplate(TestTemplate, ABC):
    def __init__(
        self,
        templates: list[TestTemplate],
        wrapper_templates: list[WrapperTestTemplateProtocol] = [],
    ) -> None:
        """
        Initialize the sequence template with a list of test templates.

        :param templates: The list of test templates to run in sequence.
        :param wrapper_templates: Optional list of wrapper templates to apply before running the test code.
        """
        self._templates = templates
        self._wrapper_templates = wrapper_templates

    @final
    async def run_test(self, exporter: TestExporter) -> None:
        """
        Run the test case by executing each template in sequence.
        :param exporter: The exporter to use for exporting test results.
        """
        async with _apply_wrapper_templates(self._wrapper_templates, exporter):
            try:
                for template in self._templates:
                    try:
                        await template.run_test(exporter)
                        await exporter.export_stage_done(self.name)
                    except BaseException as e:
                        await exporter.export_stage_exception(self.name, e)
                        raise
                await exporter.export_stage_done(self.name)
            except BaseException as e:
                await exporter.export_stage_exception(self.name, e)
                raise
