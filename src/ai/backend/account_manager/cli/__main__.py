from pathlib import Path

import click
import tomlkit
from setproctitle import setproctitle

from ai.backend.logging import LogLevel

from ..config import ServerConfig, generate_example_json
from ..utils import ensure_json_serializable


@click.group(invoke_without_command=False, context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--log-level",
    type=click.Choice([*LogLevel.__members__.keys()], case_sensitive=False),
    default="INFO",
    help="Set the logging verbosity level",
)
@click.pass_context
def main(
    ctx: click.Context,
    log_level: str,
) -> None:
    """
    Backend.AI Account Manager CLI
    """
    setproctitle("backend.ai: account-manager.cli")


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


if __name__ == "__main__":
    main()
