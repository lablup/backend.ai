from __future__ import annotations

import logging
import pprint
import time
from datetime import datetime
from typing import Any

import coloredlogs
from pythonjsonlogger.jsonlogger import JsonFormatter


def format_exception(self, ei) -> str:
    s = "".join(ei)
    if s[-1:] == "\n":
        s = s[:-1]
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
