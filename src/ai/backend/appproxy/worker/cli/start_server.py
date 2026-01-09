"""
Lightweight entry point wrapper for the app-proxy-worker start-server command.

This module provides a minimal CLI entry point that defers heavy imports
until the command is actually executed, improving CLI startup time.
"""

from __future__ import annotations

from pathlib import Path

import click


@click.command()
@click.option(
    "-f",
    "--config-path",
    "--config",
    type=Path,
    default=None,
    help=(
        "The config file path. (default: ./proxy-worker.toml and /etc/backend.ai/proxy-worker.toml)"
    ),
)
@click.option(
    "--debug",
    is_flag=True,
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
    config_path: Path | None,
    debug: bool,
    log_level: str,
) -> None:
    """
    Start the app-proxy worker service as a foreground process.

    This is a thin wrapper that defers the heavy import of server module.
    """
    from ai.backend.appproxy.worker.server import main as server_main
    from ai.backend.logging import LogLevel

    ctx.invoke(
        server_main,
        config_path=config_path,
        debug=debug,
        log_level=LogLevel[log_level.upper()],
    )
