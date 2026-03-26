"""CLI commands for resource allocation management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group()
def allocation() -> None:
    """Resource allocation commands."""


@allocation.command()
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
def search(
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
        registry = await create_v2_registry(load_v2_config())
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
