from __future__ import annotations

import logging
from contextlib import closing
from io import StringIO
from logging.handlers import QueueHandler
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from janus import _SyncQueueProxy


class RelativeCreatedFormatter(logging.Formatter):
    def format(self, record):
        record.relative_seconds = record.relativeCreated / 1000
        return super().format(record)


class BraceMessage:
    __slots__ = ("fmt", "args")

    def __init__(self, fmt, args) -> None:
        self.fmt = fmt
        self.args = args

    def __str__(self) -> str:
        return self.fmt.format(*self.args)


class BraceStyleAdapter(logging.LoggerAdapter):
    def log(self, level, msg, *args, **kwargs) -> None:
        if self.isEnabledFor(level):
            _msg, _kwargs = self.process(msg, kwargs)
            self.logger._log(level, BraceMessage(_msg, args), (), **_kwargs)


def setup_logger_basic(log_prefix: str, debug: bool) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    for handler in handlers:
        handler.setFormatter(
            RelativeCreatedFormatter(
                log_prefix + ": +{relative_seconds:,.3f} [{levelname}] {message}",
                style="{",
            )
        )
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        handlers=handlers,
    )


class LogQHandler(QueueHandler):
    def enqueue(self, record: logging.LogRecord) -> None:
        assert self.formatter is not None
        with closing(StringIO()) as buf:
            print(self.formatter.format(record), file=buf)
            if record.exc_info is not None:
                print(self.formatter.formatException(record.exc_info), file=buf)
            self.queue.put_nowait((
                b"stderr",
                buf.getvalue().encode("utf8"),
            ))


def setup_logger(
    log_queue: _SyncQueueProxy[logging.LogRecord],
    log_prefix: str,
    debug: bool,
) -> None:
    # configure logging to publish logs via outsock as well
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if not debug:
        handlers.append(LogQHandler(log_queue))
    for handler in handlers:
        handler.setFormatter(
            RelativeCreatedFormatter(
                log_prefix + ": +{relative_seconds:,.3f} [{levelname}] {message}",
                style="{",
            )
        )
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        handlers=handlers,
    )
