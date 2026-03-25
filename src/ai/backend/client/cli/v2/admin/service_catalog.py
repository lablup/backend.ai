"""Admin CLI commands for service catalogs."""

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
def service_catalog() -> None:
    """Service catalog admin commands."""


@service_catalog.command()
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option(
    "--service-group",
    default=None,
    type=str,
    help="Filter catalogs whose service group contains this substring.",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., service_group:asc, display_name:desc, registered_at:desc).",
)
def search(
    limit: int,
    offset: int,
    service_group: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search service catalog entries with admin scope."""
    from ai.backend.common.dto.manager.v2.service_catalog.request import (
        AdminSearchServiceCatalogsInput,
        ServiceCatalogFilter,
        ServiceCatalogOrder,
    )
    from ai.backend.common.dto.manager.v2.service_catalog.types import ServiceCatalogOrderField

    # Build filter only if any filter option is provided
    filter_dto: ServiceCatalogFilter | None = None
    if service_group is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = ServiceCatalogFilter(
            service_group=StringFilter(contains=service_group),
        )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, ServiceCatalogOrderField, ServiceCatalogOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = AdminSearchServiceCatalogsInput(
                filter=filter_dto,
                order=orders,
                limit=limit,
                offset=offset,
            )
            result = await registry.service_catalog.admin_search(request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
