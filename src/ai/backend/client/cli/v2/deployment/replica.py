"""User-facing CLI commands for deployment replicas."""

from __future__ import annotations

import click


@click.group()
def replica() -> None:
    """Deployment replica commands."""
