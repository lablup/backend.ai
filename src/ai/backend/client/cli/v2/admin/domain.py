"""Admin CLI commands for the v2 domain resource."""

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
def domain() -> None:
    """Admin domain commands."""


@domain.command()
@click.option("--limit", default=20, help="Maximum number of results to return.")
@click.option("--offset", default=0, help="Number of results to skip.")
@click.option(
    "--name-contains",
    default=None,
    type=str,
    help="Filter domains whose name contains this substring.",
)
@click.option(
    "--is-active/--no-is-active",
    default=None,
    help="Filter by active status.",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., name:asc, created_at:desc).",
)
def search(
    limit: int,
    offset: int,
    name_contains: str | None,
    is_active: bool | None,
    order_by: tuple[str, ...],
) -> None:
    """Search domains (superadmin only)."""
    from ai.backend.common.dto.manager.v2.domain.request import (
        AdminSearchDomainsInput,
        DomainFilter,
        DomainOrder,
    )
    from ai.backend.common.dto.manager.v2.domain.types import DomainOrderField

    # Build filter only if any filter option is provided
    filter_dto: DomainFilter | None = None
    if name_contains is not None or is_active is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = DomainFilter(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            is_active=is_active,
        )

    # Build order only if --order-by is provided
    orders = parse_order_options(order_by, DomainOrderField, DomainOrder) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.domain.admin_search(
                AdminSearchDomainsInput(
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
