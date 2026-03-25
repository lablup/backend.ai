"""CLI commands for fair share management.

Commands are organized into sub-groups: ``domain``, ``project``,
and ``user``.
"""

from __future__ import annotations

import click

from .domain import domain
from .project import project
from .user import user


@click.group(name="fair-share")
def fair_share() -> None:
    """Fair share management commands."""


# Register sub-groups
fair_share.add_command(domain)
fair_share.add_command(project)
fair_share.add_command(user)
