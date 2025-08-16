from __future__ import annotations

import logging
from collections.abc import Iterable, Iterator, Mapping, MutableMapping
from contextlib import contextmanager
from contextvars import ContextVar
from types import TracebackType
from typing import Any, LiteralString, TypeAlias, TypedDict, cast, override

from ai.backend.logging.otel import OpenTelemetrySpec

_log_context_fields: ContextVar[Mapping[str, Any]] = ContextVar("log_context_fields", default={})

__all__ = (
    "BraceMessage",
    "BraceStyleAdapter",
    "enforce_debug_logging",
    "with_log_context_fields",
)

_TRACE_LEVEL = 5
_TRACE_LEVEL_NAME = "TRACE"


def _register_custom_loglevels() -> None:
    if _TRACE_LEVEL_NAME not in logging.getLevelNamesMapping():
        logging.addLevelName(_TRACE_LEVEL, _TRACE_LEVEL_NAME)


# Taken from the typeshed module for logging
_SysExcInfoType: TypeAlias = (
    tuple[type[BaseException], BaseException, TracebackType | None] | tuple[None, None, None]
)
_ExcInfoType: TypeAlias = None | bool | _SysExcInfoType | BaseException


class ContextKWArgs(TypedDict):
    exc_info: _ExcInfoType
    stack_info: bool
    stacklevel: int
    extra: Mapping[str, object] | None


class BraceMessage:
    __slots__ = ("fmt", "args", "kwargs")

    def __init__(self, fmt: str, args: tuple[Any, ...], kwargs: Mapping[str, Any]) -> None:
        self.fmt = fmt
        self.args = args
        self.kwargs = kwargs

    def __str__(self) -> str:
        return self.fmt.format(*self.args, **self.kwargs)


class BraceStyleAdapter(logging.LoggerAdapter[logging.Logger]):
    _loggers: set[logging.Logger] = set()

    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)
        self._loggers.add(logger)

    @override
    def log(
        self,
        level: int,
        msg: object,
        *args,
        exc_info: _ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
        **user_kwargs,
    ) -> None:
        if self.isEnabledFor(level):
            context_kwargs: ContextKWArgs = {
                "exc_info": exc_info,
                "stack_info": stack_info,
                "stacklevel": stacklevel,
                "extra": extra,
            }
            msg, context_kwargs = self.process(msg, context_kwargs)  # type: ignore
            assert isinstance(msg, str)
            user_kwargs["extra"] = context_kwargs["extra"]
            self.logger._log(level, BraceMessage(msg, args, user_kwargs), (), **context_kwargs)

    @override
    def process(
        self,
        msg: object,
        kwargs: MutableMapping[str, object],
    ) -> tuple[object, MutableMapping[str, object]]:
        kwargs["stacklevel"] = cast(int, kwargs.get("stacklevel", 1)) + 1
        kwargs["extra"] = {
            **_log_context_fields.get(),
            **(cast(dict[str, Any], kwargs["extra"] or {})),
        }
        return msg, kwargs

    def trace(
        self,
        msg: LiteralString,
        *args,
        exc_info: _ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
        **kwargs,
    ) -> None:
        self.log(
            _TRACE_LEVEL,
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
            **kwargs,
        )

    @classmethod
    def apply_otel(cls, spec: OpenTelemetrySpec) -> None:
        from .otel import apply_otel_loggers

        apply_otel_loggers(cls._loggers, spec)


def enforce_debug_logging(loggers: Iterable[str]) -> None:
    # Backend.AI's daemon logging:
    # - All handlers are added to the root logger only.
    #   -> Need to override the log level of the root logger's handlers.
    # - Each logger has separate logging level.
    #   -> Need to override the log level of the individual loggers.
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.setLevel(logging.DEBUG)
    for name in loggers:
        instance = logging.getLogger(name)
        instance.setLevel(logging.DEBUG)


@contextmanager
def with_log_context_fields(fields: Mapping[str, Any]) -> Iterator[Mapping[str, Any]]:
    current_fields = _log_context_fields.get()
    new_fields = {**current_fields, **fields}
    token = _log_context_fields.set(new_fields)
    try:
        yield new_fields
    finally:
        _log_context_fields.reset(token)
