"""CLI commands for scheduling history management.

Commands are organized into sub-groups: ``session``, ``kernel``, ``deployment``,
``replica-group`` and ``route``.
"""

from __future__ import annotations

import click

from .deployment import deployment
from .kernel import kernel
from .replica_group import replica_group
from .route import route
from .session import session


@click.group(name="scheduling-history")
def scheduling_history() -> None:
    """Scheduling history commands."""


# Register sub-groups
scheduling_history.add_command(session)
scheduling_history.add_command(kernel)
scheduling_history.add_command(deployment)
scheduling_history.add_command(replica_group)
scheduling_history.add_command(route)
