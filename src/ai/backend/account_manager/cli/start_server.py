"""
Lightweight entry point wrapper for the account-manager start-server command.

This module provides a minimal CLI entry point that defers heavy imports
until the command is actually executed, improving CLI startup time.
"""

from __future__ import annotations

import click


@click.command()
@click.pass_context
def main(ctx: click.Context) -> None:
    """
    Start the account-manager service as a foreground process.

    This is a thin wrapper that defers the heavy import of server module.
    """
    from ai.backend.account_manager.server import main as server_main

    ctx.invoke(server_main)
