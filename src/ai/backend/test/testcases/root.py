import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any, AsyncIterator, Optional

from ai.backend.test.testcases.context import TestContextManager
from ai.backend.test.testcases.template import TestTemplate, WrapperTestTemplate


class TestRunContext(TestContextManager):
    """Context for the entire test run"""

    _ctxvar: ContextVar[Optional[dict[str, Any]]]

    def __init__(self) -> None:
        self._ctxvar = ContextVar("test_run_context", default=None)

    def get_current(self) -> Any:
        return super().get_current()

    def get_test_id(self) -> str:
        return self.get_current()["test_id"]


test_run_context = TestRunContext()


class RootTestTemplate(WrapperTestTemplate):
    """A root test template for wrapper test template that generate test name and id for each test run."""

    _template: TestTemplate
    _test_id: uuid.UUID

    def __init__(self, template: TestTemplate) -> None:
        self._template = template
        self._test_id = uuid.uuid4()

    @property
    def name(self) -> str:
        return f"{self._template.name}-{self._test_id}"

    @asynccontextmanager
    async def context(self) -> AsyncIterator[None]:
        test_info = {
            "test_id": str(self._test_id),
        }
        async with test_run_context.with_current(test_info):
            yield
