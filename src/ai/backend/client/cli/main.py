import warnings

import click

from ai.backend.cli.extensions import ExtendedCommandGroup
from ai.backend.client import __version__
from ai.backend.client.cli.types import CLIContext, OutputMode
from ai.backend.client.config import APIConfig, set_config
from ai.backend.client.output import get_output_handler


@click.group(
    cls=ExtendedCommandGroup,
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
)
@click.option(
    "--skip-sslcert-validation",
    help="Skip SSL certificate validation for all API requests.",
    is_flag=True,
)
@click.option(
    "--output",
    type=click.Choice(["json", "console"]),
    default="console",
    help="Set the output style of the command results.",
)
@click.version_option(version=__version__)
@click.pass_context
def main(ctx: click.Context, skip_sslcert_validation: bool, output: str) -> None:
    """
    Backend.AI command line interface.
    """
    from .announcement import announce

    config = APIConfig(
        skip_sslcert_validation=skip_sslcert_validation,
        announcement_handler=announce,
    )
    set_config(config)

    output_mode = OutputMode(output)
    cli_ctx = CLIContext(
        api_config=config,
        output_mode=output_mode,
    )
    cli_ctx.output = get_output_handler(cli_ctx, output_mode)
    ctx.obj = cli_ctx

    from .pretty import show_warning

    warnings.showwarning = show_warning
