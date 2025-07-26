import asyncio
import logging
from typing import LiteralString, cast

from ai.backend.logging.utils import BraceMessage


class BraceStyleAdapter(logging.LoggerAdapter):
    def __init__(self, logger, extra=None):
        super().__init__(logger, extra)

    def log(self, level, msg, *args, **kwargs):
        if self.isEnabledFor(level):
            msg, kwargs = self.process(msg, kwargs)
            kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + 1
            try:
                if (_current_task := asyncio.current_task()) and (
                    _request_id := getattr(_current_task, "request_id", None)
                ):
                    msg = cast(LiteralString, f"#{_request_id} - {msg}")
            except RuntimeError:
                pass  # no running event loop, just skip
            self.logger._log(level, BraceMessage(msg, args), (), **kwargs)
