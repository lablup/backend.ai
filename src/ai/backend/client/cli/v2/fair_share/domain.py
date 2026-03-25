"""CLI commands for domain fair share."""

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
    """Domain fair share commands."""


@domain.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option("--resource-group", default=None, type=str, help="Filter by resource group name.")
@click.option("--domain-name", default=None, type=str, help="Filter by domain name.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., fair_share_factor:desc, domain_name:asc).",
)
def search(
    limit: int | None,
    offset: int | None,
    resource_group: str | None,
    domain_name: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search domain fair shares."""
    from ai.backend.common.dto.manager.v2.fair_share.request import (
        DomainFairShareFilter,
        DomainFairShareOrder,
        SearchDomainFairSharesInput,
    )
    from ai.backend.common.dto.manager.v2.fair_share.types import DomainFairShareOrderField

    # Build filter only if any filter option is provided
    filter_dto: DomainFairShareFilter | None = None
    if resource_group is not None or domain_name is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = DomainFairShareFilter(
            resource_group=StringFilter(contains=resource_group)
            if resource_group is not None
            else None,
            domain_name=StringFilter(contains=domain_name) if domain_name is not None else None,
        )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, DomainFairShareOrderField, DomainFairShareOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.fair_share.search_domain(
                SearchDomainFairSharesInput(
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


@domain.command()
@click.option("--resource-group", required=True, help="Scaling group name.")
@click.option("--domain-name", required=True, help="Domain name.")
def get(resource_group: str, domain_name: str) -> None:
    """Get a single domain fair share record."""
    from ai.backend.common.dto.manager.v2.fair_share.request import GetDomainFairShareInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.fair_share.get_domain(
                GetDomainFairShareInput(
                    resource_group=resource_group,
                    domain_name=domain_name,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
