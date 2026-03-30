"""User-facing CLI commands for the v2 image domain."""

from __future__ import annotations

import click


@click.group()
def image() -> None:
    """Image management commands."""
