"""CLI commands for RBAC role management."""

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
    """RBAC role commands."""


@role.command()
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
def search(
    limit: int | None,
    offset: int | None,
    order_by: tuple[str, ...],
    name_contains: str | None,
    source: str | None,
    status: str | None,
) -> None:
    """Search roles."""
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

    # Build filter only if any filter option is provided
    filter_dto: RoleFilter | None = None
    if any([name_contains is not None, source is not None, status is not None]):
        filter_dto = RoleFilter(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            source=RoleSourceFilter(equals=source) if source is not None else None,
            status=RoleStatusFilter(equals=status) if status is not None else None,
        )

    # Build order only if --order-by is provided
    orders = parse_order_options(order_by, RoleOrderField, RoleOrderBy) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.rbac.search_roles(
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


@role.command(name="project-search")
@click.argument("project_id", type=str)
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
def project_search(
    project_id: str,
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
                UUID(project_id),
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


@role.command()
@click.argument("role_id", type=str)
def get(role_id: str) -> None:
    """Get a role by UUID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.rbac.get_role(UUID(role_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@role.command()
@click.option("--name", required=True, help="Role name.")
@click.option("--description", default=None, help="Role description.")
def create(name: str, description: str | None) -> None:
    """Create a new role."""
    from ai.backend.common.dto.manager.v2.rbac.request import CreateRoleInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.rbac.create_role(
                CreateRoleInput(name=name, description=description),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@role.command()
@click.argument("role_id", type=str)
def delete(role_id: str) -> None:
    """Soft-delete a role."""
    from ai.backend.common.dto.manager.v2.rbac.request import DeleteRoleInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.rbac.delete_role(
                DeleteRoleInput(id=UUID(role_id)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
