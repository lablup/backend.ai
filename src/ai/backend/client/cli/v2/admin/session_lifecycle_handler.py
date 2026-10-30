"""Admin CLI commands for the session lifecycle handler registry."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    print_result,
)


@click.group(name="session-lifecycle-handler")
def session_lifecycle_handler() -> None:
    """Admin session lifecycle handler commands."""


@session_lifecycle_handler.command(name="list")
def list_() -> None:
    """List all registered session lifecycle handlers (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.session_lifecycle_handler.admin_list()
        finally:
            await registry.close()
        print_result(result)

    asyncio.run(_run())
