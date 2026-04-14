"""Resource group commands.

All resource group operations require superadmin privileges.
Use ``./bai admin resource-group {command}`` instead.
"""

from __future__ import annotations

import click


@click.group(name="resource-group")
def resource_group() -> None:
    """Resource group commands (use 'admin resource-group' for all operations)."""
