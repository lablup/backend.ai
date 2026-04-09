"""CLI commands for the v2 project resource."""

from __future__ import annotations

import asyncio
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group()
def project() -> None:
    """Project commands."""


@project.command()
@click.argument("project_id", type=click.UUID)
def get(project_id: UUID) -> None:
    """Get a project by UUID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.project.get(project_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# -- Sub-group: role --


@project.group()
def role() -> None:
    """Project-scoped role commands."""


@role.command(name="search")
@click.argument("project_id", type=click.UUID)
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., name:asc, created_at:desc).",
)
@click.option("--name-contains", type=str, default=None, help="Filter roles by name (contains).")
@click.option(
    "--source",
    type=click.Choice(["system", "custom"], case_sensitive=False),
    default=None,
    help="Filter by role source.",
)
@click.option(
    "--status",
    type=click.Choice(["active", "inactive", "deleted"], case_sensitive=False),
    default=None,
    help="Filter by role status.",
)
def role_search(
    project_id: UUID,
    limit: int | None,
    offset: int | None,
    order_by: tuple[str, ...],
    name_contains: str | None,
    source: str | None,
    status: str | None,
) -> None:
    """Search roles registered in a project scope."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.rbac.request import (
        RoleFilter,
        RoleOrderBy,
        SearchRolesInput,
    )
    from ai.backend.common.dto.manager.v2.rbac.types import (
        RoleOrderField,
        RoleSourceFilter,
        RoleStatusFilter,
    )

    filter_dto: RoleFilter | None = None
    if any([name_contains is not None, source is not None, status is not None]):
        filter_dto = RoleFilter(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            source=RoleSourceFilter(equals=source) if source is not None else None,
            status=RoleStatusFilter(equals=status) if status is not None else None,
        )

    orders = parse_order_options(order_by, RoleOrderField, RoleOrderBy) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.rbac.project_search_roles(
                project_id,
                SearchRolesInput(
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
