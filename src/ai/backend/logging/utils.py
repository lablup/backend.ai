from __future__ import annotations

import logging
from collections.abc import Iterable
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Generator, LiteralString, Mapping

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


class BraceMessage:
    __slots__ = ("fmt", "args")

    def __init__(self, fmt: LiteralString, args: tuple[Any, ...]):
        self.fmt = fmt
        self.args = args

    def __str__(self):
        return self.fmt.format(*self.args)


class BraceStyleAdapter(logging.LoggerAdapter):
    _loggers: set[logging.Logger] = set()

    def __init__(self, logger, extra=None):
        super().__init__(logger, extra)
        self._loggers.add(logger)

    def log(self, level, msg, *args, **kwargs):
        if self.isEnabledFor(level):
            msg, kwargs = self.process(msg, kwargs)
            kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + 1
            kwargs["extra"] = {
                **_log_context_fields.get(),
            }
            self.logger._log(level, BraceMessage(msg, args), (), **kwargs)

    def trace(self, msg, *args, **kwargs):
        self.log(_TRACE_LEVEL, msg, *args, **kwargs)

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
def with_log_context_fields(fields: Mapping[str, Any]) -> Generator[Mapping[str, Any], None, None]:
    current_fields = _log_context_fields.get()
    new_fields = {**current_fields, **fields}
    token = _log_context_fields.set(new_fields)
    try:
        yield new_fields
    finally:
        _log_context_fields.reset(token)
