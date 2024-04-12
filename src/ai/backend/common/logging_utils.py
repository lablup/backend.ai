import logging
from collections.abc import Iterable
from typing import Any, LiteralString

__all__ = (
    "BraceMessage",
    "BraceStyleAdapter",
    "enforce_debug_logging",
)


class BraceMessage:
    __slots__ = ("fmt", "args")

    def __init__(self, fmt: LiteralString, args: tuple[Any, ...]):
        self.fmt = fmt
        self.args = args

    def __str__(self):
        return self.fmt.format(*self.args)


class BraceStyleAdapter(logging.LoggerAdapter):
    def __init__(self, logger, extra=None):
        super().__init__(logger, extra)

    def log(self, level, msg, *args, **kwargs):
        if self.isEnabledFor(level):
            msg, kwargs = self.process(msg, kwargs)
            kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + 1
            self.logger._log(level, BraceMessage(msg, args), (), **kwargs)


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
