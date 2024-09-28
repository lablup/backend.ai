from pathlib import Path

import click
import tomlkit
from setproctitle import setproctitle

from ai.backend.common.cli import LazyGroup
from ai.backend.logging import LogLevel

from ..config import ServerConfig, generate_example_json
from ..utils import ensure_json_serializable
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
        path_type=Path,
    ),
    default=None,
    help="The config file path. (default: ./account-manager.conf and /etc/backend.ai/account-manager.conf)",
)
@click.option(
    "--log-level",
    type=click.Choice([*LogLevel.__members__.keys()], case_sensitive=False),
    default="INFO",
    help="Set the logging verbosity level",
)
@click.pass_context
def main(
    ctx: click.Context,
    config_path: Path | None,
    log_level: str,
) -> None:
    """
    Backend.AI Account Manager CLI
    """
    setproctitle("backend.ai: account-manager.cli")
    ctx.obj = ctx.with_resource(CLIContext(config_path, log_level))


@main.command()
@click.option(
    "--output",
    "-o",
    default="-",
    type=click.Path(dir_okay=False, writable=True),
    help="Output file path (default: stdout)",
)
def generate_example_configuration(output: Path) -> None:
    """
    Generates example TOML configuration file for Backend.AI Account Manager.
    """
    generated_example = generate_example_json(ServerConfig)
    if output == "-" or output is None:
        print(tomlkit.dumps(ensure_json_serializable(generated_example)))
    else:
        with open(output, mode="w") as fw:
            fw.write(tomlkit.dumps(ensure_json_serializable(generated_example)))


@main.group(cls=LazyGroup, import_name="ai.backend.account_manager.cli.fixture:cli")
def fixture():
    """Command set for managing fixtures."""


if __name__ == "__main__":
    main()
