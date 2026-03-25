"""CLI commands for resource usage management.

Commands are organized into sub-groups: ``domain``, ``project``,
and ``user``.
"""

from __future__ import annotations

import click

from .domain import domain
from .project import project
from .user import user


@click.group(name="resource-usage")
def resource_usage() -> None:
    """Resource usage commands."""


# Register sub-groups
resource_usage.add_command(domain)
resource_usage.add_command(project)
resource_usage.add_command(user)
