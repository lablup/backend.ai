from contextlib import contextmanager
from contextvars import ContextVar
from typing import Generic, Iterator, Optional, TypeVar, final

T = TypeVar("T")


class BaseTestContext(Generic[T]):
    """
    Base class for tester's context management.
    This class provides a way to manage context variables for test scenarios.
    It uses `contextvars` to store the current value and provides methods to get and set this value.
    It is designed to be subclassed for specific test contexts.
    """

    _ctxvar: Optional[ContextVar[Optional[T]]] = None

    def __init_subclass__(cls):
        if cls._ctxvar is not None:
            raise RuntimeError(f"{cls.__name__} is already initialized")
        cls._ctxvar = ContextVar[T](f"{cls.__name__}_ctxvar", default=None)

    @classmethod
    @final
    def get_current(cls) -> T:
        """
        Get the current value from context
        :raises RuntimeError: if no value is set in the context (Tester must set it before using)
        """
        if cls._ctxvar is None:
            raise RuntimeError("Don't use BaseTestContext directly, subclass it instead")
        res = cls._ctxvar.get()
        if res is None:
            raise RuntimeError(f"No value is set in {cls.__class__.__name__} tester context")
        return res

    @classmethod
    @final
    @contextmanager
    def with_current(cls, value: T) -> Iterator[None]:
        """Set the current value in the context"""
        if cls._ctxvar is None:
            raise RuntimeError("Don't use BaseTestContext directly, subclass it instead")
        token = cls._ctxvar.set(value)
        try:
            yield
        finally:
            cls._ctxvar.reset(token)
