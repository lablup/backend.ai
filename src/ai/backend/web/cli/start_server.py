"""
Lightweight entry point wrapper for the web start-server command.

This module provides a minimal CLI entry point that defers heavy imports
until the command is actually executed, improving CLI startup time.
"""

from __future__ import annotations

from pathlib import Path

import click


@click.command()
@click.option(
    "-f",
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default="webserver.conf",
    help="The configuration file to use.",
)
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    help="A shortcut to set `--log-level=DEBUG`",
)
@click.option(
    "--log-level",
    type=click.Choice(
        ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE", "NOTSET"],
        case_sensitive=False,
    ),
    default="NOTSET",
    help="Set the logging verbosity level",
)
@click.pass_context
def main(
    ctx: click.Context,
    config_path: Path,
    debug: bool,
    log_level: str,
) -> None:
    """
    Start the web service as a foreground process.

    This is a thin wrapper that defers the heavy import of server module.
    """
    from ai.backend.logging import LogLevel
    from ai.backend.web.server import main as server_main

    ctx.invoke(
        server_main,
        config_path=config_path,
        debug=debug,
        log_level=LogLevel[log_level.upper()],
    )
