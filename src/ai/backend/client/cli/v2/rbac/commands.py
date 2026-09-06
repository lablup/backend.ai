"""CLI commands for RBAC management.

Commands are organized into sub-groups: ``role``, ``permission``,
``assignment``, and ``entity``.
"""

from __future__ import annotations

import click

from .assignment import assignment
from .entity import entity
from .permission import permission
from .role import role


@click.group()
def rbac() -> None:
    """RBAC management commands."""


# Register sub-groups
rbac.add_command(role)
rbac.add_command(permission)
rbac.add_command(assignment)
rbac.add_command(entity)
