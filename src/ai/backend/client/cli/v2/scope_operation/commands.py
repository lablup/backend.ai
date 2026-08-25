"""CLI commands for the v2 scope operation domain."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    print_result,
)


@click.group(name="scope-operation")
def scope_operation() -> None:
    """Scope operation commands."""


@scope_operation.command(name="list")
def list_() -> None:
    """List every operation the wiring targets by scope."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.scope_operation.list()
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
