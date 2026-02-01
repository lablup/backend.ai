from __future__ import annotations

import logging
from collections.abc import Mapping
from types import TracebackType
from typing import Any


class BraceMessage:
    __slots__ = ("args", "fmt")

    def __init__(self, fmt: str, args: tuple[Any, ...]) -> None:
        self.fmt = fmt
        self.args = args

    def __str__(self) -> str:
        return self.fmt.format(*self.args)


class BraceStyleAdapter(logging.LoggerAdapter[logging.Logger]):
    def __init__(self, logger: logging.Logger, extra: Mapping[str, Any] | None = None) -> None:
        super().__init__(logger, extra)

    def log(
        self,
        level: int,
        msg: object,
        *args: object,
        exc_info: (
            bool
            | tuple[type[BaseException], BaseException, TracebackType | None]
            | tuple[None, None, None]
            | BaseException
            | None
        ) = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
        **kwargs: object,
    ) -> None:
        if self.isEnabledFor(level):
            msg, processed_kwargs = self.process(msg, kwargs)
            self.logger._log(level, BraceMessage(str(msg), args), (), **processed_kwargs)
