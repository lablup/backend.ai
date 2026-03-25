"""CLI commands for resource slot management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2._helpers import create_v2_registry, print_result


@click.group()
def resource_slots() -> None:
    """Resource slot management commands."""


@resource_slots.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@pass_ctx_obj
def search_slot_types(ctx: CLIContext, limit: int | None, offset: int | None) -> None:
    """Search resource slot types."""
    from ai.backend.common.dto.manager.v2.resource_slot.request import (
        AdminSearchResourceSlotTypesInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.resource_slot.search_slot_types(
                AdminSearchResourceSlotTypesInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_slots.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@pass_ctx_obj
def search_agent_resources(ctx: CLIContext, limit: int | None, offset: int | None) -> None:
    """Search agent resources."""
    from ai.backend.common.dto.manager.v2.resource_slot.request import (
        AdminSearchAgentResourcesInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.resource_slot.search_agent_resources(
                AdminSearchAgentResourcesInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_slots.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@pass_ctx_obj
def search_allocations(ctx: CLIContext, limit: int | None, offset: int | None) -> None:
    """Search resource allocations."""
    from ai.backend.common.dto.manager.v2.resource_slot.request import (
        AdminSearchResourceAllocationsInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.resource_slot.search_allocations(
                AdminSearchResourceAllocationsInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
