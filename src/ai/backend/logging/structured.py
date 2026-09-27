from __future__ import annotations

import logging
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from types import MappingProxyType, TracebackType
from typing import ClassVar, LiteralString
from uuid import UUID

__all__ = (
    "LogFieldNormalizer",
    "LogValue",
    "StructuredLogger",
    "with_log_context",
)

type LogValue = str | int | float | bool | None | UUID | Enum | Path | Decimal | datetime
type _NormalizedLogValue = str | int | float | bool | None
type _ExcInfo = (
    None
    | bool
    | BaseException
    | tuple[type[BaseException], BaseException, TracebackType | None]
    | tuple[None, None, None]
)

_TRACE_LEVEL = 5

_log_context: ContextVar[Mapping[str, _NormalizedLogValue]] = ContextVar(
    "structured_log_context", default=MappingProxyType({})
)


class LogFieldNormalizer:
    _name_prefix: ClassVar[str] = "log_tag_"

    def normalize(self, fields: Mapping[str, LogValue]) -> dict[str, _NormalizedLogValue]:
        return {
            self.normalize_name(name): self.normalize_value(value) for name, value in fields.items()
        }

    def normalize_name(self, name: str) -> str:
        return f"{self._name_prefix}{name}"

    def normalize_value(self, value: LogValue) -> _NormalizedLogValue:
        match value:
            case Enum():
                return self.normalize_value(value.value)
            case UUID() | Path() | Decimal():
                return str(value)
            case datetime():
                return value.isoformat()
            case _:
                return value


class StructuredLogger:
    _logger: logging.Logger
    _normalizer: LogFieldNormalizer

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        self._normalizer = LogFieldNormalizer()

    def trace(
        self, msg: LiteralString, /, *args: object, stacklevel: int = 1, **fields: LogValue
    ) -> None:
        self._emit(_TRACE_LEVEL, msg, args, fields, exc_info=None, stacklevel=stacklevel)

    def debug(
        self, msg: LiteralString, /, *args: object, stacklevel: int = 1, **fields: LogValue
    ) -> None:
        self._emit(logging.DEBUG, msg, args, fields, exc_info=None, stacklevel=stacklevel)

    def info(self, msg: LiteralString, /, *, stacklevel: int = 1, **fields: LogValue) -> None:
        self._emit(logging.INFO, msg, (), fields, exc_info=None, stacklevel=stacklevel)

    def warning(
        self,
        msg: LiteralString,
        /,
        *,
        exc_info: _ExcInfo = None,
        stacklevel: int = 1,
        **fields: LogValue,
    ) -> None:
        self._emit(logging.WARNING, msg, (), fields, exc_info=exc_info, stacklevel=stacklevel)

    def error(
        self,
        msg: LiteralString,
        /,
        *,
        exc_info: _ExcInfo = None,
        stacklevel: int = 1,
        **fields: LogValue,
    ) -> None:
        self._emit(logging.ERROR, msg, (), fields, exc_info=exc_info, stacklevel=stacklevel)

    def exception(self, msg: LiteralString, /, *, stacklevel: int = 1, **fields: LogValue) -> None:
        self._emit(logging.ERROR, msg, (), fields, exc_info=True, stacklevel=stacklevel)

    def _emit(
        self,
        level: int,
        msg: str,
        args: tuple[object, ...],
        fields: Mapping[str, LogValue],
        *,
        exc_info: _ExcInfo,
        stacklevel: int,
    ) -> None:
        if not self._logger.isEnabledFor(level):
            return
        extra = {**_log_context.get(), **self._normalizer.normalize(fields)}
        message = msg.format(*args) if args else msg
        # +2 skips this method and the level method.
        self._logger.log(level, message, exc_info=exc_info, extra=extra, stacklevel=stacklevel + 2)


@contextmanager
def with_log_context(**fields: LogValue) -> Iterator[None]:
    token = _log_context.set({**_log_context.get(), **LogFieldNormalizer().normalize(fields)})
    try:
        yield
    finally:
        _log_context.reset(token)
