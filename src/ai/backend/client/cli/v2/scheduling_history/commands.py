"""CLI commands for scheduling history management.

Commands are organized into sub-groups: ``session``, ``deployment``,
and ``route``.
"""

from __future__ import annotations

import click

from .deployment import deployment
from .route import route
from .session import session


@click.group(name="scheduling-history")
def scheduling_history() -> None:
    """Scheduling history commands."""


# Register sub-groups
scheduling_history.add_command(session)
scheduling_history.add_command(deployment)
scheduling_history.add_command(route)
