from pathlib import Path
from typing import Self

import click

from ai.backend.common.logging import AbstractLogger, LocalLogger

from ..config import ServerConfig
from ..config import load as load_config


class CLIContext:
    _local_config: ServerConfig | None
    _logger: AbstractLogger

    def __init__(self, config_path: Path, log_level: str) -> None:
        self.config_path = config_path
        self.log_level = log_level
        self._local_config = None

    @property
    def local_config(self) -> ServerConfig:
        # Lazy-load the configuration only when requested.
        if self._local_config is None:
            self._local_config = load_config(self.config_path, self.log_level)
        return self._local_config

    def __enter__(self) -> Self:
        # The "start-server" command is injected by ai.backend.cli from the entrypoint
        # and it has its own multi-process-aware logging initialization.
        # If we duplicate the local logging with it, the process termination may hang.
        click_ctx = click.get_current_context()
        if click_ctx.invoked_subcommand != "start-server":
            self._logger = LocalLogger({})
            self._logger.__enter__()
        return self

    def __exit__(self, *exc_info) -> None:
        click_ctx = click.get_current_context()
        if click_ctx.invoked_subcommand != "start-server":
            self._logger.__exit__()
