from __future__ import annotations

import pathlib
from typing import Optional

import click

from ai.backend.common.cli import LazyGroup

from .context import CLIContext

# LogLevel values for click.Choice - avoid importing ai.backend.logging at module level
_LOG_LEVELS = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE", "NOTSET"]


@click.group(invoke_without_command=False, context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "-f",
    "--config-path",
    "--config",
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        exists=True,
        path_type=pathlib.Path,
    ),
    default=None,
    help="The config file path. (default: ./manager.conf and /etc/backend.ai/manager.conf)",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Set the logging level to DEBUG",
)
@click.option(
    "--log-level",
    type=click.Choice(_LOG_LEVELS, case_sensitive=False),
    default="NOTSET",
    help="Set the logging verbosity level",
)
@click.pass_context
def main(
    ctx: click.Context,
    log_level: str,
    debug: bool,
    config_path: Optional[pathlib.Path] = None,
) -> None:
    """The root entrypoint for unified CLI of agent"""
    from setproctitle import setproctitle

    from ai.backend.logging.types import LogLevel

    setproctitle("backend.ai: agent.cli")
    if debug:
        log_level = "DEBUG"

    ctx.obj = ctx.with_resource(CLIContext(config_path=config_path, log_level=LogLevel(log_level)))


@main.group(cls=LazyGroup, import_name="ai.backend.agent.cli.config:cli")
def config() -> None:
    """Command set for configuration management."""


@main.group(cls=LazyGroup, import_name="ai.backend.agent.cli.dependencies:cli")
def dependencies() -> None:
    """Command set for dependency verification and validation."""


@main.group(cls=LazyGroup, import_name="ai.backend.agent.cli.health:cli")
def health() -> None:
    """Command set for health checking."""
