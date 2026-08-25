"""CLI commands for the v2 entity type domain."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    print_result,
)


@click.group(name="entity-type")
def entity_type() -> None:
    """Entity type commands."""


@entity_type.command(name="list")
def list_() -> None:
    """List every entity type a request may name."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.entity_type.list()
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
