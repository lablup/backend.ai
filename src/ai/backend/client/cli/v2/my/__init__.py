"""Self-service CLI command group for v2 REST API.

Registers self-service sub-groups per entity under
``backend.ai v2 my {entity} {command}``.
"""

from __future__ import annotations

import click

from ai.backend.common.cli import LazyGroup


@click.group()
def my() -> None:
    """Self-service commands for the current user."""


@my.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.my.keypair:keypair")
def keypair() -> None:
    """My keypair commands."""


@my.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.my.login_history:login_history",
)
def login_history() -> None:
    """My login history commands."""


@my.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.my.login_session:login_session",
)
def login_session() -> None:
    """My login session commands."""
