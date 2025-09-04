from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any, Optional, Self

import click

from ai.backend.logging import AbstractLogger, LocalLogger, LogLevel


class CLIContext(AbstractContextManager):
    _logger: AbstractLogger

    def __init__(self, log_level: LogLevel, config_path: Optional[Path] = None) -> None:
        self.data: dict[str, Any] = {}
        self.config_path = config_path
        self.log_level = log_level

    def __enter__(self) -> Self:
        # The "start-server" command is injected by ai.backend.cli from the entrypoint
        # and it has its own multi-process-aware logging initialization.
        # If we duplicate the local logging with it, the process termination may hang.
        click_ctx = click.get_current_context()
        if click_ctx.invoked_subcommand != "start-server":
            self._logger = LocalLogger(log_level=self.log_level)
            self._logger.__enter__()
        return self

    def __exit__(self, *exc_info) -> None:
        click_ctx = click.get_current_context()
        if click_ctx.invoked_subcommand != "start-server":
            self._logger.__exit__()
