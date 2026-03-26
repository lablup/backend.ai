"""User-facing CLI commands for the v2 session domain."""

from __future__ import annotations

import click


@click.group()
def session() -> None:
    """Session management commands."""
