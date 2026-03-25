"""Admin CLI commands for the v2 project resource."""

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
def project() -> None:
    """Admin project commands."""


@project.command()
@click.option("--limit", default=20, help="Maximum number of results to return.")
@click.option("--offset", default=0, help="Number of results to skip.")
@click.option(
    "--name-contains",
    default=None,
    type=str,
    help="Filter projects whose name contains this substring.",
)
@click.option("--domain-name", default=None, type=str, help="Filter by exact domain name.")
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
    domain_name: str | None,
    is_active: bool | None,
    order_by: tuple[str, ...],
) -> None:
    """Search projects (superadmin only)."""
    from ai.backend.common.dto.manager.v2.group.request import (
        AdminSearchGroupsInput,
        GroupFilter,
        GroupOrder,
    )
    from ai.backend.common.dto.manager.v2.group.types import GroupOrderField

    # Build filter only if any filter option is provided
    filter_dto: GroupFilter | None = None
    if any(opt is not None for opt in (name_contains, domain_name, is_active)):
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = GroupFilter(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            domain_name=StringFilter(equals=domain_name) if domain_name is not None else None,
            is_active=is_active,
        )

    # Build order only if --order-by is provided
    orders = parse_order_options(order_by, GroupOrderField, GroupOrder) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.project.admin_search(
                AdminSearchGroupsInput(
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
