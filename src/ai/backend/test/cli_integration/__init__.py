from __future__ import annotations

import click

from ..cli.context import CLIContext


@click.group()
@click.pass_obj
def cli(cli_context: CLIContext) -> None:
    """CLI-based integration tests"""
    pass
