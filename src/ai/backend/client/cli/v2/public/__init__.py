"""Anonymous CLI command group for v2 REST API.

Registers sub-groups per entity under ``backend.ai v2 public {entity} {command}``.
``public`` sits where ``admin`` and ``my`` sit — it is the scope a command acts at, not
an operation. Commands here name no principal and need no credentials, so they are the
only ones usable before login.
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
