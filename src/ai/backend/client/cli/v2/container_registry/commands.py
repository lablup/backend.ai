"""CLI commands for the v2 container registry domain.

Admin-only commands (search) are under ``admin container-registry``.
"""

from __future__ import annotations

import click


@click.group(name="container-registry")
def container_registry() -> None:
    """Container registry management commands."""
