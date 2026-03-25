"""CLI commands for the v2 agent resource.

All agent commands are admin-only and have been moved to the admin group.
This module is kept as a placeholder for potential future user-facing agent commands.
"""

from __future__ import annotations

import click


@click.group()
def agent() -> None:
    """Agent commands."""
