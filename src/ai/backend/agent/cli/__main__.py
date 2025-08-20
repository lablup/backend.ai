from __future__ import annotations

import pathlib
from typing import Optional

import click
from setproctitle import setproctitle

from ai.backend.common.cli import LazyGroup
from ai.backend.logging import LogLevel

from .context import CLIContext


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
    type=click.Choice([*LogLevel], case_sensitive=False),
    default=LogLevel.NOTSET,
    help="Set the logging verbosity level",
)
@click.pass_context
def main(
    ctx: click.Context,
    log_level: LogLevel,
    debug: bool,
    config_path: Optional[pathlib.Path] = None,
) -> None:
    """The root entrypoint for unified CLI of agent"""
    setproctitle("backend.ai: agent.cli")
    if debug:
        log_level = LogLevel.DEBUG

    ctx.obj = ctx.with_resource(CLIContext(config_path=config_path, log_level=log_level))


@main.group(cls=LazyGroup, import_name="ai.backend.agent.cli.config:cli")
def config() -> None:
    """Command set for configuration management."""
