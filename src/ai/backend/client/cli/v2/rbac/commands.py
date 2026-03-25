"""CLI commands for RBAC management."""

from __future__ import annotations

import asyncio
from uuid import UUID

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2.helpers import create_v2_registry, parse_order_options, print_result


@click.group()
def rbac() -> None:
    """RBAC management commands."""


# ------------------------------------------------------------------ Roles


@rbac.command()
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
@pass_ctx_obj
def search_roles(
    ctx: CLIContext,
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
        AdminSearchRolesGQLInput,
        RoleFilter,
        RoleOrderBy,
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
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.rbac.search_roles(
                AdminSearchRolesGQLInput(
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


@rbac.command()
@click.argument("role_id", type=str)
@pass_ctx_obj
def get_role(ctx: CLIContext, role_id: str) -> None:
    """Get a role by UUID."""

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.rbac.get_role(UUID(role_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@rbac.command()
@click.option("--name", required=True, help="Role name.")
@click.option("--description", default=None, help="Role description.")
@pass_ctx_obj
def create_role(ctx: CLIContext, name: str, description: str | None) -> None:
    """Create a new role."""
    from ai.backend.common.dto.manager.v2.rbac.request import CreateRoleInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.rbac.create_role(
                CreateRoleInput(name=name, description=description),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@rbac.command()
@click.argument("role_id", type=str)
@pass_ctx_obj
def delete_role(ctx: CLIContext, role_id: str) -> None:
    """Soft-delete a role."""
    from ai.backend.common.dto.manager.v2.rbac.request import DeleteRoleInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.rbac.delete_role(
                DeleteRoleInput(id=UUID(role_id)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# ------------------------------------------------------------------ Permissions


@rbac.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., id:asc, entity_type:desc).",
)
@click.option("--role-id", type=str, default=None, help="Filter by role UUID.")
@click.option("--scope-type", type=str, default=None, help="Filter by scope type (e.g., domain).")
@click.option(
    "--entity-type", type=str, default=None, help="Filter by entity type (e.g., session)."
)
@pass_ctx_obj
def search_permissions(
    ctx: CLIContext,
    limit: int | None,
    offset: int | None,
    order_by: tuple[str, ...],
    role_id: str | None,
    scope_type: str | None,
    entity_type: str | None,
) -> None:
    """Search permissions."""
    from ai.backend.common.dto.manager.v2.rbac.request import (
        AdminSearchPermissionsGQLInput,
        PermissionFilter,
        PermissionOrderBy,
    )
    from ai.backend.common.dto.manager.v2.rbac.types import PermissionOrderField

    # Build filter only if any filter option is provided
    filter_dto: PermissionFilter | None = None
    if any([role_id is not None, scope_type is not None, entity_type is not None]):
        filter_dto = PermissionFilter(
            role_id=UUID(role_id) if role_id is not None else None,
            scope_type=scope_type,
            entity_type=entity_type,
        )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, PermissionOrderField, PermissionOrderBy) if order_by else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.rbac.search_permissions(
                AdminSearchPermissionsGQLInput(
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


# ------------------------------------------------------------------ Assignments


@rbac.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., username:asc, granted_at:desc).",
)
@click.option("--role-id", type=str, default=None, help="Filter by role UUID.")
@click.option("--username-contains", type=str, default=None, help="Filter by username (contains).")
@click.option("--email-contains", type=str, default=None, help="Filter by email (contains).")
@pass_ctx_obj
def search_assignments(
    ctx: CLIContext,
    limit: int | None,
    offset: int | None,
    order_by: tuple[str, ...],
    role_id: str | None,
    username_contains: str | None,
    email_contains: str | None,
) -> None:
    """Search role assignments."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.rbac.request import (
        AdminSearchRoleAssignmentsGQLInput,
        RoleAssignmentFilter,
        RoleAssignmentOrderBy,
    )
    from ai.backend.common.dto.manager.v2.rbac.types import RoleAssignmentOrderField

    # Build filter only if any filter option is provided
    filter_dto: RoleAssignmentFilter | None = None
    if any([role_id is not None, username_contains is not None, email_contains is not None]):
        filter_dto = RoleAssignmentFilter(
            role_id=UUID(role_id) if role_id is not None else None,
            username=(
                StringFilter(contains=username_contains) if username_contains is not None else None
            ),
            email=(StringFilter(contains=email_contains) if email_contains is not None else None),
        )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, RoleAssignmentOrderField, RoleAssignmentOrderBy)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.rbac.search_assignments(
                AdminSearchRoleAssignmentsGQLInput(
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


@rbac.command()
@click.option("--user-id", required=True, help="User UUID to assign the role to.")
@click.option("--role-id", required=True, help="Role UUID to assign.")
@pass_ctx_obj
def assign_role(ctx: CLIContext, user_id: str, role_id: str) -> None:
    """Assign a role to a user."""
    from ai.backend.common.dto.manager.v2.rbac.request import AssignRoleInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.rbac.assign_role(
                AssignRoleInput(user_id=UUID(user_id), role_id=UUID(role_id)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@rbac.command()
@click.option("--user-id", required=True, help="User UUID to revoke the role from.")
@click.option("--role-id", required=True, help="Role UUID to revoke.")
@pass_ctx_obj
def revoke_role(ctx: CLIContext, user_id: str, role_id: str) -> None:
    """Revoke a role from a user."""
    from ai.backend.common.dto.manager.v2.rbac.request import RevokeRoleInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.rbac.revoke_role(
                RevokeRoleInput(user_id=UUID(user_id), role_id=UUID(role_id)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# ------------------------------------------------------------------ Entities


@rbac.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., entity_type:asc, registered_at:desc).",
)
@click.option(
    "--entity-type", type=str, default=None, help="Filter by entity type (e.g., session, vfolder)."
)
@pass_ctx_obj
def search_entities(
    ctx: CLIContext,
    limit: int | None,
    offset: int | None,
    order_by: tuple[str, ...],
    entity_type: str | None,
) -> None:
    """Search entity associations."""
    from ai.backend.common.dto.manager.v2.rbac.request import (
        AdminSearchEntitiesGQLInput,
        EntityFilter,
        EntityOrderBy,
    )
    from ai.backend.common.dto.manager.v2.rbac.types import EntityOrderField

    # Build filter only if any filter option is provided
    filter_dto: EntityFilter | None = None
    if entity_type is not None:
        filter_dto = EntityFilter(
            entity_type=entity_type,
        )

    # Build order only if --order-by is provided
    orders = parse_order_options(order_by, EntityOrderField, EntityOrderBy) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.rbac.search_entities(
                AdminSearchEntitiesGQLInput(
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
