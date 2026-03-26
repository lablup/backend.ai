"""CLI commands for agent resource management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group(name="agent-resource")
def agent_resource() -> None:
    """Agent resource commands."""


@agent_resource.command()
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
def search(
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
        registry = await create_v2_registry(load_v2_config())
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
