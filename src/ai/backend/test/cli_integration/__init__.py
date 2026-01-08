from __future__ import annotations

import click

from ai.backend.test.cli.context import CLIContext


@click.group()
@click.pass_obj
def cli(cli_context: CLIContext) -> None:
    """CLI-based integration tests"""
    pass
