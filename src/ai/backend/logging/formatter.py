from __future__ import annotations

import logging
import pprint
import time
import traceback
from collections.abc import Sequence
from datetime import datetime
from types import TracebackType
from typing import Any, TypeAlias, cast

import coloredlogs
from pythonjsonlogger.json import JsonFormatter

_SysExcInfoType: TypeAlias = (
    tuple[type[BaseException], BaseException, TracebackType | None] | tuple[None, None, None]
)


def format_exception(self, ei: Sequence[str] | _SysExcInfoType) -> str:
    match ei:
        case (str(), *_):
            # Already foramtted from the source process for ease of serialization
            s = "".join(cast(Sequence[str], ei))  # cast is required for mypy
        case (type(), BaseException(), _):
            # A live exc_info object from the current process
            s = "".join(traceback.format_exception(*ei))
        case _:
            s = "<exception-info-unavailable>"
    s = s.rstrip("\n")
    return s


class SerializedExceptionFormatter(logging.Formatter):
    def formatException(self, ei) -> str:
        return format_exception(self, ei)


class ConsoleFormatter(logging.Formatter):
    def formatException(self, ei) -> str:
        return format_exception(self, ei)

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        ct = self.converter(record.created)  # type: ignore
        if datefmt:
            datefmt = datefmt.replace("%f", f"{int(record.msecs):03d}")
            return time.strftime(datefmt, ct)
        else:
            t = time.strftime("%Y-%m-%d %H:%M:%S", ct)
            return f"{t}.{int(record.msecs):03d}"


class CustomJsonFormatter(JsonFormatter):
    def formatException(self, ei) -> str:
        return format_exception(self, ei)

    def add_fields(
        self,
        log_record: dict[str, Any],  # the manipulated entry object
        record: logging.LogRecord,  # the source log record
        message_dict: dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        if not log_record.get("timestamp"):
            # this doesn't use record.created, so it is slightly off
            now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            log_record["timestamp"] = now
        if loglevel := log_record.get("level"):
            log_record["level"] = loglevel.upper()
        else:
            log_record["level"] = record.levelname.upper()


class ColorizedFormatter(coloredlogs.ColoredFormatter):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        coloredlogs.logging.Formatter.formatException = format_exception


class pretty:
    """A simple object wrapper to pretty-format it when formatting the log record."""

    def __init__(self, obj: Any) -> None:
        self.obj = obj

    def __repr__(self) -> str:
        return pprint.pformat(self.obj)
