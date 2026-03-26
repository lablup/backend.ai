"""User-facing CLI commands for deployment revisions."""

from __future__ import annotations

import click


@click.group()
def revision() -> None:
    """Deployment revision commands."""
