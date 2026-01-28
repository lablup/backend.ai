from __future__ import annotations

import functools
import inspect
from collections.abc import Callable, Iterable
from typing import Any

from ai.backend.client.output.types import FieldSet, FieldSpec
from ai.backend.client.session import AsyncSession, Session, api_session

__all__ = (
    "APIFunctionMeta",
    "BaseFunction",
    "api_function",
    "resolve_fields",
)


def _wrap_method(cls: type, orig_name: str, meth: Callable) -> Callable:
    @functools.wraps(meth)
    def _method(*args: Any, **kwargs: Any) -> Any:
        # We need to keep the original attributes so that they could be correctly
        # bound to the class/instance at runtime.
        func = getattr(cls, orig_name)
        coro = func(*args, **kwargs)
        _api_session = api_session.get()
        if _api_session is None:
            raise RuntimeError(
                "API functions must be called inside the context of a valid API session",
            )
        if isinstance(_api_session, AsyncSession):
            return coro
        # At this point, _api_session must be a Session (the sync version)
        if not isinstance(_api_session, Session):
            raise RuntimeError("API session must be either AsyncSession or Session")
        if inspect.isasyncgen(coro):
            return _api_session.worker_thread.execute_generator(coro)
        return _api_session.worker_thread.execute(coro)

    return _method


def api_function[T: Callable](meth: T) -> T:
    """
    Mark the wrapped method as the API function method.
    """
    meth._backend_api = True  # type: ignore[attr-defined]
    return meth


def resolve_fields(
    fields: Iterable[FieldSpec | str] | None,
    base_field_set: FieldSet,
    default_fields: Iterable[FieldSpec],
) -> tuple[str, ...]:
    if fields is None:
        fields = default_fields
    return tuple(
        f.field_ref if isinstance(f, FieldSpec) else base_field_set[f].field_ref for f in fields
    )


def field_resolver(
    base_field_set: FieldSet,
    default_fields: Iterable[FieldSpec],
) -> Callable:
    def decorator(meth: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if fields := kwargs.get("fields", default_fields):
                resolved_fields = tuple(
                    f.field_ref if isinstance(f, FieldSpec) else base_field_set[f].field_ref
                    for f in fields
                )
                kwargs["fields"] = resolved_fields
            return meth(*args, **kwargs)

        return wrapper

    return decorator


class APIFunctionMeta(type):
    """
    Converts all methods marked with :func:`api_function` into
    session-aware methods that are either plain Python functions
    or coroutines.
    """

    _async = True

    def __init__(
        cls, name: str, bases: tuple[type, ...], attrs: dict[str, Any], **kwargs: Any
    ) -> None:
        super().__init__(name, bases, attrs)
        for attr_name, attr_value in attrs.items():
            if hasattr(attr_value, "_backend_api"):
                orig_name = "_orig_" + attr_name
                setattr(cls, orig_name, attr_value)
                wrapped = _wrap_method(cls, orig_name, attr_value)
                setattr(cls, attr_name, wrapped)


class BaseFunction(metaclass=APIFunctionMeta):
    pass
