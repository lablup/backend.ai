from collections.abc import Mapping
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
    _used: Mapping[str, "BaseTestContext"] = {}

    def __init_subclass__(cls):
        if cls._ctxvar is not None:
            raise RuntimeError(f"{cls.__name__} is already initialized")
        cls._ctxvar = ContextVar[T](f"{cls.__name__}_ctxvar", default=None)
        cls._used[cls.get_name()] = cls

    @classmethod
    def get_name(cls) -> str:
        """
        Get the name of the context
        :return: name of the context
        """
        raise NotImplementedError(
            f"{cls.__name__} must implement get_name method to return the context name"
        )

    @classmethod
    def get_used_contexts(cls) -> Mapping[str, "BaseTestContext"]:
        """
        Get all used contexts
        :return: mapping of context names to context instances
        """
        return cls._used

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
            raise RuntimeError(f'No value is set in "{cls.get_name()}" context')
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
