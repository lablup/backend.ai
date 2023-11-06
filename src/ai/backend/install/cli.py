import click

from ai.backend.install import __version__

from .types import InstallModes


@click.command(
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
)
@click.option(
    "--mode",
    type=click.Choice(InstallModes._member_names_, case_sensitive=False),
    default=None,
    help="Override the installation mode. [default: auto-detect]",
)
@click.version_option(version=__version__)
@click.pass_context
def main(
    ctx: click.Context,
    mode: InstallModes | None,
) -> None:
    """The installer"""
    print(f"installer main: {mode}")
