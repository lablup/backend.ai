"""CLI commands for resource slot management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2.helpers import create_v2_registry, parse_order_options, print_result


@click.group()
def resource_slots() -> None:
    """Resource slot management commands."""


@resource_slots.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--slot-name",
    default=None,
    type=str,
    help="Filter slot types whose slot name contains this substring.",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., slot_name:asc, rank:desc).",
)
@pass_ctx_obj
def search_slot_types(
    ctx: CLIContext,
    limit: int | None,
    offset: int | None,
    slot_name: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search resource slot types."""
    from ai.backend.common.dto.manager.v2.resource_slot.request import (
        AdminSearchResourceSlotTypesInput,
        ResourceSlotTypeFilter,
        ResourceSlotTypeOrder,
    )
    from ai.backend.common.dto.manager.v2.resource_slot.types import ResourceSlotTypeOrderField

    # Build filter only if any filter option is provided
    filter_dto: ResourceSlotTypeFilter | None = None
    if slot_name is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = ResourceSlotTypeFilter(
            slot_name=StringFilter(contains=slot_name),
        )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, ResourceSlotTypeOrderField, ResourceSlotTypeOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.resource_slot.search_slot_types(
                AdminSearchResourceSlotTypesInput(
                    filter=filter_dto,
                    order=orders,
                    limit=limit,
                    offset=offset,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_slots.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--agent-id",
    default=None,
    type=str,
    help="Filter agent resources whose agent ID contains this substring.",
)
@click.option(
    "--slot-name",
    default=None,
    type=str,
    help="Filter agent resources whose slot name contains this substring.",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., agent_id:asc, slot_name:desc).",
)
@pass_ctx_obj
def search_agent_resources(
    ctx: CLIContext,
    limit: int | None,
    offset: int | None,
    agent_id: str | None,
    slot_name: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search agent resources."""
    from ai.backend.common.dto.manager.v2.resource_slot.request import (
        AdminSearchAgentResourcesInput,
        AgentResourceFilter,
        AgentResourceOrder,
    )
    from ai.backend.common.dto.manager.v2.resource_slot.types import AgentResourceOrderField

    # Build filter only if any filter option is provided
    filter_dto: AgentResourceFilter | None = None
    if agent_id is not None or slot_name is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = AgentResourceFilter(
            agent_id=StringFilter(contains=agent_id) if agent_id is not None else None,
            slot_name=StringFilter(contains=slot_name) if slot_name is not None else None,
        )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, AgentResourceOrderField, AgentResourceOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.resource_slot.search_agent_resources(
                AdminSearchAgentResourcesInput(
                    filter=filter_dto,
                    order=orders,
                    limit=limit,
                    offset=offset,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_slots.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--slot-name",
    default=None,
    type=str,
    help="Filter allocations whose slot name contains this substring.",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., kernel_id:asc, slot_name:desc).",
)
@pass_ctx_obj
def search_allocations(
    ctx: CLIContext,
    limit: int | None,
    offset: int | None,
    slot_name: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search resource allocations."""
    from ai.backend.common.dto.manager.v2.resource_slot.request import (
        AdminSearchResourceAllocationsInput,
        ResourceAllocationFilter,
        ResourceAllocationOrder,
    )
    from ai.backend.common.dto.manager.v2.resource_slot.types import ResourceAllocationOrderField

    # Build filter only if any filter option is provided
    filter_dto: ResourceAllocationFilter | None = None
    if slot_name is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = ResourceAllocationFilter(
            slot_name=StringFilter(contains=slot_name),
        )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, ResourceAllocationOrderField, ResourceAllocationOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.resource_slot.search_allocations(
                AdminSearchResourceAllocationsInput(
                    filter=filter_dto,
                    order=orders,
                    limit=limit,
                    offset=offset,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
