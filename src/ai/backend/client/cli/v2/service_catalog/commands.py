"""CLI commands for the v2 service catalog domain.

Admin-only commands (search) are under ``admin service-catalog``.
"""

from __future__ import annotations

import click


@click.group(name="service-catalog")
def service_catalog() -> None:
    """Service catalog management commands."""
