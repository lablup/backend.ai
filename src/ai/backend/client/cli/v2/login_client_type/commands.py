"""CLI commands for the v2 login client type domain.

User-facing commands (get). Admin-only commands (create, search, update, delete)
are under ``admin login-client-type``.
"""

from __future__ import annotations

import asyncio
import uuid

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    print_result,
)


@click.group(name="login-client-type")
def login_client_type() -> None:
    """Login client type management commands."""


@login_client_type.command()
@click.argument("login_client_type_id", type=click.UUID)
def get(login_client_type_id: uuid.UUID) -> None:
    """Get a login client type by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.login_client_type.get(login_client_type_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
