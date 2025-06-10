import uuid
from contextlib import asynccontextmanager as actxmgr
from contextvars import ContextVar
from typing import Any, AsyncIterator, Optional

from ai.backend.test.testcases.context import BaseTestContext
from ai.backend.test.testcases.template import TestTemplate, WrapperTestTemplate


class TestRunContext(BaseTestContext[dict[str, Any]]):
    """Context for the entire test run"""

    _ctxvar: ContextVar[Optional[dict[str, Any]]] = ContextVar("test_run_context", default=None)

    @classmethod
    def get_test_id(cls) -> str:
        return cls.get_current()["test_id"]


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

    @actxmgr
    async def context(self) -> AsyncIterator[None]:
        test_info = {
            "test_id": str(self._test_id),
        }
        async with TestRunContext.with_current(test_info):
            yield
