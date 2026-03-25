"""CLI commands for domain resource usage."""

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
    """Domain resource usage commands."""


@domain.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option("--domain-name", default=None, help="Filter by domain name.")
@click.option("--resource-group", default=None, help="Filter by resource group.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., period_start:desc).",
)
def search(
    limit: int | None,
    offset: int | None,
    domain_name: str | None,
    resource_group: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search domain usage buckets."""
    from ai.backend.common.dto.manager.v2.resource_usage.request import (
        AdminSearchDomainUsageBucketsInput,
    )

    # Note: AdminSearchDomainUsageBucketsInput does not support order;
    # --order-by is accepted for forward compatibility but currently ignored
    # when the DTO does not expose an order field.
    if order_by:
        from ai.backend.common.dto.manager.v2.resource_usage.request import (
            DomainUsageBucketOrderBy,
        )
        from ai.backend.common.dto.manager.v2.resource_usage.types import UsageBucketOrderField

        _orders = parse_order_options(order_by, UsageBucketOrderField, DomainUsageBucketOrderBy)
        # The admin search input does not accept order yet; silently drop.
        _ = _orders

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_usage.search_domain_usage(
                AdminSearchDomainUsageBucketsInput(
                    domain_name=domain_name,
                    resource_group=resource_group,
                    limit=limit,
                    offset=offset,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
