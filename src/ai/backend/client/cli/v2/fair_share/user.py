"""CLI commands for user fair share."""

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
    """User fair share commands."""


@user.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option("--resource-group", default=None, type=str, help="Filter by resource group name.")
@click.option("--domain-name", default=None, type=str, help="Filter by domain name.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., fair_share_factor:desc, user_username:asc).",
)
def search(
    limit: int | None,
    offset: int | None,
    resource_group: str | None,
    domain_name: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search user fair shares."""
    from ai.backend.common.dto.manager.v2.fair_share.request import (
        SearchUserFairSharesInput,
        UserFairShareFilter,
        UserFairShareOrder,
    )
    from ai.backend.common.dto.manager.v2.fair_share.types import UserFairShareOrderField

    # Build filter only if any filter option is provided
    filter_dto: UserFairShareFilter | None = None
    if resource_group is not None or domain_name is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = UserFairShareFilter(
            resource_group=StringFilter(contains=resource_group)
            if resource_group is not None
            else None,
            domain_name=StringFilter(contains=domain_name) if domain_name is not None else None,
        )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, UserFairShareOrderField, UserFairShareOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.fair_share.search_user(
                SearchUserFairSharesInput(
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


@user.command()
@click.option("--resource-group", required=True, help="Scaling group name.")
@click.option("--project-id", required=True, help="Project UUID.")
@click.option("--user-uuid", required=True, help="User UUID.")
def get(resource_group: str, project_id: str, user_uuid: str) -> None:
    """Get a single user fair share record."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.fair_share.request import GetUserFairShareInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.fair_share.get_user(
                GetUserFairShareInput(
                    resource_group=resource_group,
                    project_id=UUID(project_id),
                    user_uuid=UUID(user_uuid),
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
