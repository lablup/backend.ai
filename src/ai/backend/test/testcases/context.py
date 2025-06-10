from contextlib import asynccontextmanager as actxmgr
from contextvars import ContextVar
from typing import Any, AsyncIterator, Generic, Optional, TypeVar

T = TypeVar("T")


class BaseTestContext(Generic[T]):
    """Base class for test context managers"""

    _ctxvar: ContextVar[Optional[T]]

    @classmethod
    def get_current(cls) -> T:
        """Get the current value from context"""
        res = cls._ctxvar.get()
        if res is None:
            raise RuntimeError(f"No value is set in {cls.__class__.__name__}")
        return res

    @classmethod
    @actxmgr
    async def with_current(cls, value: Any) -> AsyncIterator[None]:
        """Set the current value in the context"""
        token = cls._ctxvar.set(value)
        try:
            yield
        finally:
            cls._ctxvar.reset(token)
