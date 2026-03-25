"""CLI commands for resource slot management.

Commands are organized into sub-groups: ``slot-type``,
``agent-resource``, and ``allocation``.
"""

from __future__ import annotations

import click

from .agent_resource import agent_resource
from .allocation import allocation
from .slot_type import slot_type


@click.group(name="resource-slot")
def resource_slot() -> None:
    """Resource slot management commands."""


# Register sub-groups
resource_slot.add_command(slot_type)
resource_slot.add_command(agent_resource)
resource_slot.add_command(allocation)
