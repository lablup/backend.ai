"""Self-service CLI commands for storage hosts."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    print_result,
)


@click.group()
def storage_host() -> None:
    """My storage host commands."""


@storage_host.command(name="permissions")
def my_storage_host_permissions() -> None:
    """List storage hosts and the permissions granted to me."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.storage_host.my_storage_host_permissions()
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
