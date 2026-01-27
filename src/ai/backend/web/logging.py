from __future__ import annotations

import logging


class BraceMessage:
    __slots__ = ("args", "fmt")

    def __init__(self, fmt, args) -> None:
        self.fmt = fmt
        self.args = args

    def __str__(self) -> str:
        return self.fmt.format(*self.args)


class BraceStyleAdapter(logging.LoggerAdapter):
    def __init__(self, logger, extra=None) -> None:
        super().__init__(logger, extra)

    def log(self, level, msg, *args, **kwargs) -> None:
        if self.isEnabledFor(level):
            msg, processed_kwargs = self.process(msg, kwargs)
            self.logger._log(level, BraceMessage(msg, args), (), **processed_kwargs)
