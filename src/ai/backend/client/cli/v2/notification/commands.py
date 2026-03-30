"""CLI commands for notification management.

Commands are organized into sub-groups: ``channel`` and ``rule``.
"""

from __future__ import annotations

import click

from .channel import channel
from .rule import rule


@click.group()
def notification() -> None:
    """Notification management commands."""


# Register sub-groups
notification.add_command(channel)
notification.add_command(rule)
