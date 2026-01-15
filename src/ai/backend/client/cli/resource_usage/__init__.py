"""Resource Usage CLI package."""

import click


@click.group()
def resource_usage() -> None:
    """Resource usage history operations (superadmin only)."""


from . import commands  # noqa
