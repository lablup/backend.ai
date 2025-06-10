from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any, AsyncIterator, Generic, Optional, TypeVar

T = TypeVar("T")


class TestContextManager(Generic[T]):
    """Base class for test context managers"""

    _ctxvar: ContextVar[Optional[T]]

    def get_current(self) -> T:
        """Get the current value from context"""
        res = self._ctxvar.get()
        if res is None:
            raise RuntimeError(f"No value is set in {self.__class__.__name__}")
        return res

    def get_or_none(self) -> Optional[T]:
        """Get the current value from context or None if not set"""
        return self._ctxvar.get()

    @asynccontextmanager
    async def with_current(self, value: Any) -> AsyncIterator[None]:
        """Set the current value in the context"""
        token = self._ctxvar.set(value)
        try:
            yield
        finally:
            self._ctxvar.reset(token)
