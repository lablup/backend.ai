"""CLI commands for RBAC entity management."""

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
def entity() -> None:
    """RBAC entity commands."""


@entity.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., entity_type:asc, registered_at:desc).",
)
@click.option(
    "--entity-type", type=str, default=None, help="Filter by entity type (e.g., session, vfolder)."
)
def search(
    limit: int | None,
    offset: int | None,
    order_by: tuple[str, ...],
    entity_type: str | None,
) -> None:
    """Search entity associations."""
    from ai.backend.common.dto.manager.v2.rbac.request import (
        AdminSearchEntitiesGQLInput,
        EntityFilter,
        EntityOrderBy,
    )
    from ai.backend.common.dto.manager.v2.rbac.types import EntityOrderField

    # Build filter only if any filter option is provided
    filter_dto: EntityFilter | None = None
    if entity_type is not None:
        filter_dto = EntityFilter(
            entity_type=entity_type,
        )

    # Build order only if --order-by is provided
    orders = parse_order_options(order_by, EntityOrderField, EntityOrderBy) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.rbac.search_entities(
                AdminSearchEntitiesGQLInput(
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
