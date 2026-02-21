from typing import Any

import click

from .completion import get_completion_command
from .extensions import ExtendedCommandGroup
from .types import CliContextInfo


@click.group(
    cls=ExtendedCommandGroup,
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
)
@click.option(
    "--skip-sslcert-validation",
    help="(client option) Skip SSL certificate validation for all API requests.",
    is_flag=True,
)
@click.option(
    "--output",
    type=click.Choice(["json", "console"]),
    default="console",
    help="(client option) Set the output style of the command results.",
)
@click.pass_context
def main(ctx: click.Context, /, **kwargs: Any) -> None:
    """Unified Command Line Interface for Backend.ai"""
    ctx.obj = CliContextInfo(info=kwargs)


# Add completion command (lazy loading to avoid import issues)
@main.command()
@click.option(
    "--shell",
    type=click.Choice(["bash", "zsh", "fish"], case_sensitive=False),
    default=None,
    help="The shell type. If not provided, it will be auto-detected.",
)
@click.option(
    "--show",
    is_flag=True,
    help="Show the completion script instead of installing it.",
)
def completion(shell, show):
    """Install or show shell completion script."""
    # Import and call the completion command only when needed
    cmd = get_completion_command("backend.ai")
    return cmd.callback(shell, show)
