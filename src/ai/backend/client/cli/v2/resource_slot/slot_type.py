"""CLI commands for resource slot type management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group(name="slot-type")
def slot_type() -> None:
    """Resource slot type commands."""


@slot_type.command()
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
def search(
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
        registry = await create_v2_registry(load_v2_config())
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
