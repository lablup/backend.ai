import click

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
def main(ctx: click.Context, **kwargs) -> None:
    """Unified Command Line Interface for Backend.ai"""
    ctx.obj = CliContextInfo(info=kwargs)
