from contextvars import ContextVar

from ai.backend.test.testcases.context import BaseTestContext


class ComputeSessionContext(BaseTestContext[str]):
    _ctxvar: ContextVar[str] = ContextVar("compute_session_name")
