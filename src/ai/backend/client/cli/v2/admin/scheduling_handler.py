"""Admin CLI commands for the deployment scheduling handler registry."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    print_result,
)


@click.group(name="scheduling-handler")
def scheduling_handler() -> None:
    """Admin scheduling-handler commands."""


@scheduling_handler.command(name="list")
def list_() -> None:
    """List all registered deployment scheduling handlers (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.scheduling_handler.list()
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
