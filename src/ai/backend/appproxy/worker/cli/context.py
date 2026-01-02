from __future__ import annotations

from contextlib import AbstractContextManager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Self

import click

if TYPE_CHECKING:
    from ai.backend.logging import AbstractLogger
    from ai.backend.logging.types import LogLevel


class CLIContext(AbstractContextManager):
    _logger: AbstractLogger

    def __init__(self, log_level: LogLevel, config_path: Optional[Path] = None) -> None:
        self.config_path = config_path
        self.log_level = log_level

    def __enter__(self) -> Self:
        from ai.backend.logging import LocalLogger

        # The "start-server" command is injected by ai.backend.cli from the entrypoint
        # and it has its own multi-process-aware logging initialization.
        # If we duplicate the local logging with it, the process termination may hang.
        click_ctx = click.get_current_context()
        if click_ctx.invoked_subcommand != "start-server":
            self._logger = LocalLogger(log_level=self.log_level)
            self._logger.__enter__()
        return self

    def __exit__(self, *exc_info: Any) -> None:
        click_ctx = click.get_current_context()
        if click_ctx.invoked_subcommand != "start-server":
            self._logger.__exit__()
