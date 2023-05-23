import functools
import inspect
from typing import Iterable

from ..output.types import FieldSet, FieldSpec
from ..session import AsyncSession, api_session

__all__ = (
    "APIFunctionMeta",
    "BaseFunction",
    "api_function",
    "resolve_fields",
)


def _wrap_method(cls, orig_name, meth):
    @functools.wraps(meth)
    def _method(*args, **kwargs):
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
        else:
            if inspect.isasyncgen(coro):
                return _api_session.worker_thread.execute_generator(coro)
            else:
                return _api_session.worker_thread.execute(coro)

    return _method


def api_function(meth):
    """
    Mark the wrapped method as the API function method.
    """
    setattr(meth, "_backend_api", True)
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
):
    def decorator(meth):
        def wrapper(*args, **kwargs):
            if fields := kwargs.get("fields", default_fields):
                resolved_fields = tuple(
                    f.field_ref if isinstance(f, FieldSpec) else base_field_set[f].field_ref
                    for f in fields
                )
                kwargs["fields"] = resolved_fields
            result = meth(*args, **kwargs)
            return result

        return wrapper

    return decorator


class APIFunctionMeta(type):
    """
    Converts all methods marked with :func:`api_function` into
    session-aware methods that are either plain Python functions
    or coroutines.
    """

    _async = True

    def __init__(cls, name, bases, attrs, **kwargs):
        super().__init__(name, bases, attrs)
        for attr_name, attr_value in attrs.items():
            if hasattr(attr_value, "_backend_api"):
                orig_name = "_orig_" + attr_name
                setattr(cls, orig_name, attr_value)
                wrapped = _wrap_method(cls, orig_name, attr_value)
                setattr(cls, attr_name, wrapped)


class BaseFunction(metaclass=APIFunctionMeta):
    pass
