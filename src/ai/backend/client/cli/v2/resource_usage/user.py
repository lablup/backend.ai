"""CLI commands for user resource usage."""

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
def user() -> None:
    """User resource usage commands."""


@user.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option("--domain-name", default=None, help="Filter by domain name.")
@click.option("--resource-group", default=None, help="Filter by resource group.")
@click.option("--project-id", default=None, help="Filter by project ID.")
@click.option("--user-uuid", default=None, help="Filter by user UUID.")
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
    project_id: str | None,
    user_uuid: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search user usage buckets."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.resource_usage.request import (
        AdminSearchUserUsageBucketsInput,
    )

    # Note: AdminSearchUserUsageBucketsInput does not support order;
    # --order-by is accepted for forward compatibility but currently ignored.
    if order_by:
        from ai.backend.common.dto.manager.v2.resource_usage.request import UserUsageBucketOrderBy
        from ai.backend.common.dto.manager.v2.resource_usage.types import UsageBucketOrderField

        _orders = parse_order_options(order_by, UsageBucketOrderField, UserUsageBucketOrderBy)
        _ = _orders

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_usage.search_user_usage(
                AdminSearchUserUsageBucketsInput(
                    domain_name=domain_name,
                    resource_group=resource_group,
                    project_id=UUID(project_id) if project_id else None,
                    user_uuid=UUID(user_uuid) if user_uuid else None,
                    limit=limit,
                    offset=offset,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
