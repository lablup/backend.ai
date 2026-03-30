"""User-facing CLI commands for deployment policies."""

from __future__ import annotations

import click


@click.group()
def policy() -> None:
    """Deployment policy commands."""
