"""Anonymous CLI command group for v2 REST API.

Registers sub-groups per entity under ``backend.ai v2 public {entity} {command}``.
``public`` occupies the same slot as ``admin`` and ``my`` — the scope a command acts at,
never the operation — so the operation keeps its standard name underneath it.

This is not a general RBAC scope: app config is the one entity with a pre-login read, and
this group exists for it. Do not add an entity here without an endpoint the manager
genuinely serves unauthenticated.
"""

from __future__ import annotations

import click

from ai.backend.common.cli import LazyGroup


@click.group()
def public() -> None:
    """Anonymous commands, usable without credentials."""


@public.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.public.app_config:app_config",
    name="app-config",
)
def app_config() -> None:
    """Public app config commands."""
