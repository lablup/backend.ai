from __future__ import annotations

import pathlib

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
    config_path: pathlib.Path | None = None,
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


@main.group(cls=LazyGroup, import_name="ai.backend.agent.cli.kernel:cli")
def kernel() -> None:
    """Command set for driving kernel RPC on a running agent (parity verification)."""


@main.command(name="start-privnet")
@click.pass_obj
def start_privnet(cli_ctx: CLIContext) -> None:
    """Start the privileged session-network daemon.

    The daemon ships with the data-plane backends it serves, so this reports its absence rather
    than failing on an import: a node with no backend installed has no helper to start either.
    """
    try:
        from ai.backend.agent.network.privnet.__main__ import (  # pants: no-infer-dep
            main as privnet_main,
        )
    except ImportError as e:
        raise click.ClickException(
            "the privileged session-network daemon is not installed on this node"
            f" ({e}); install the cluster-network backend package that provides it"
        ) from e

    privnet_main(cli_ctx.config_path)
