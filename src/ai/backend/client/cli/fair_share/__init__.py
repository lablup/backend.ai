"""Fair Share CLI package."""

import click


@click.group()
def fair_share() -> None:
    """Fair share scheduler operations (superadmin only)."""


from . import commands  # noqa
