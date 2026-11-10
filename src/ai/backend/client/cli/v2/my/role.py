"""CLI commands for self-service role operations."""

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
def role() -> None:
    """My role commands."""


@role.command()
@click.option("--limit", default=None, type=int, help="Maximum number of results to return.")
@click.option("--offset", default=None, type=int, help="Number of results to skip.")
@click.option("--first", default=None, type=int, help="Cursor-based: return first N items.")
@click.option("--after", default=None, type=str, help="Cursor-based: return items after cursor.")
@click.option("--last", default=None, type=int, help="Cursor-based: return last N items.")
@click.option("--before", default=None, type=str, help="Cursor-based: return items before cursor.")
@click.option("--role-id", type=click.UUID, default=None, help="Filter by role UUID.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., granted_at:desc).",
)
def search(
    limit: int | None,
    offset: int | None,
    first: int | None,
    after: str | None,
    last: int | None,
    before: str | None,
    role_id: UUID | None,
    order_by: tuple[str, ...],
) -> None:
    """Search my role assignments."""
    from ai.backend.common.dto.manager.query import UUIDFilter
    from ai.backend.common.dto.manager.v2.rbac.request import (
        RoleAssignmentFilter,
        RoleAssignmentOrderBy,
        SearchRoleAssignmentsInput,
    )
    from ai.backend.common.dto.manager.v2.rbac.types import RoleAssignmentOrderField

    filter_dto: RoleAssignmentFilter | None = None
    if role_id is not None:
        filter_dto = RoleAssignmentFilter(
            role_id=UUIDFilter(equals=role_id),
        )

    orders = (
        parse_order_options(order_by, RoleAssignmentOrderField, RoleAssignmentOrderBy)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = SearchRoleAssignmentsInput(
                filter=filter_dto,
                order=orders,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            )
            result = await registry.rbac.my_search_assignments(request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@role.command(name="list")
@click.option("--limit", default=None, type=int, help="Maximum number of results to return.")
@click.option("--offset", default=None, type=int, help="Number of results to skip.")
@click.option("--first", default=None, type=int, help="Cursor-based: return first N items.")
@click.option("--after", default=None, type=str, help="Cursor-based: return items after cursor.")
@click.option("--last", default=None, type=int, help="Cursor-based: return last N items.")
@click.option("--before", default=None, type=str, help="Cursor-based: return items before cursor.")
@click.option("--name", type=str, default=None, help="Filter by role name.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., created_at:desc).",
)
def list_roles(
    limit: int | None,
    offset: int | None,
    first: int | None,
    after: str | None,
    last: int | None,
    before: str | None,
    name: str | None,
    order_by: tuple[str, ...],
) -> None:
    """List the roles I hold."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.rbac.request import (
        RoleFilter,
        RoleOrderBy,
        SearchRolesInput,
    )
    from ai.backend.common.dto.manager.v2.rbac.types import RoleOrderField

    filter_dto: RoleFilter | None = None
    if name is not None:
        filter_dto = RoleFilter(name=StringFilter(equals=name))

    orders = parse_order_options(order_by, RoleOrderField, RoleOrderBy) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = SearchRolesInput(
                filter=filter_dto,
                order=orders,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            )
            result = await registry.rbac.my_search_roles(request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
