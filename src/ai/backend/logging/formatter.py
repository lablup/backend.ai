from __future__ import annotations

import json
import logging
import pprint
import time
import traceback
from collections.abc import Sequence
from datetime import UTC, datetime
from types import TracebackType
from typing import Any, cast, override

import coloredlogs
from pythonjsonlogger.json import JsonFormatter

from ai.backend.logging.structured import LogFieldNormalizer

type _SysExcInfoType = (
    tuple[type[BaseException], BaseException, TracebackType | None] | tuple[None, None, None]
)


def append_log_fields(message: str, record: logging.LogRecord) -> str:
    normalizer = LogFieldNormalizer()
    normalized_fields = normalizer.normalized_fields_of(record)
    if not normalized_fields:
        return message
    rendered_fields = " ".join(
        f"{normalizer.field_name_of(name)}={_render_field_value(value)}"
        for name, value in normalized_fields.items()
    )
    return f"{message} {rendered_fields}"


def _render_field_value(value: object) -> str:
    if isinstance(value, str) and (not value or any(c.isspace() or c in '"=' for c in value)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def format_exception(
    _self: logging.Formatter,
    ei: Sequence[str] | _SysExcInfoType,
) -> str:
    match ei:
        case (str(), *_):
            # Already foramtted from the source process for ease of serialization
            s = "".join(cast(Sequence[str], ei))  # cast is required for mypy
        case (type(), BaseException(), _):
            # A live exc_info object from the current process
            s = "".join(traceback.format_exception(*ei))
        case _:
            s = "<exception-info-unavailable>"
    return s.rstrip("\n")


class SerializedExceptionFormatter(logging.Formatter):
    @override
    def formatException(self, ei: Sequence[str] | _SysExcInfoType) -> str:
        return format_exception(self, ei)


class ConsoleFormatter(logging.Formatter):
    @override
    def formatMessage(self, record: logging.LogRecord) -> str:
        return append_log_fields(super().formatMessage(record), record)

    @override
    def formatException(self, ei: Sequence[str] | _SysExcInfoType) -> str:
        return format_exception(self, ei)

    @override
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        ct = self.converter(record.created)
        if datefmt:
            datefmt = datefmt.replace("%f", f"{int(record.msecs):03d}")
            return time.strftime(datefmt, ct)
        t = time.strftime("%Y-%m-%d %H:%M:%S", ct)
        return f"{t}.{int(record.msecs):03d}"


class CustomJsonFormatter(JsonFormatter):
    @override
    def formatException(self, ei: Sequence[str] | _SysExcInfoType) -> str:
        return format_exception(self, ei)

    @override
    def add_fields(
        self,
        log_record: dict[str, Any],  # the manipulated entry object
        record: logging.LogRecord,  # the source log record
        message_dict: dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        if not log_record.get("timestamp"):
            # this doesn't use record.created, so it is slightly off
            now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            log_record["timestamp"] = now
        if loglevel := log_record.get("level"):
            log_record["level"] = loglevel.upper()
        else:
            log_record["level"] = record.levelname.upper()


class ColorizedFormatter(coloredlogs.ColoredFormatter):  # type: ignore[misc]
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        coloredlogs.logging.Formatter.formatException = format_exception

    @override
    def formatMessage(self, record: logging.LogRecord) -> str:
        return append_log_fields(super().formatMessage(record), record)


class pretty:
    """A simple object wrapper to pretty-format it when formatting the log record."""

    def __init__(self, obj: Any) -> None:
        self.obj = obj

    @override
    def __repr__(self) -> str:
        return pprint.pformat(self.obj)
