import click

from ai.backend.cli.extensions import ExtendedCommandGroup


@click.group(
    cls=ExtendedCommandGroup,
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
)
def main() -> None:
    """
    Anchor for the ``backendai_cli_v10`` entry point registered under the ``_`` key.

    Importing this module imports the ``ai.backend.client.cli`` package, whose
    ``__init__`` registers every client command group onto ``ai.backend.cli.main:main``.
    That import side effect is the entry point's only purpose: ``ai.backend.cli.loader``
    copies just ``.commands`` off the loaded group and drops its params and callback,
    so anything declared here would never run.
    """
