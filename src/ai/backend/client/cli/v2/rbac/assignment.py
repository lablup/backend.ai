"""CLI commands for RBAC assignment management."""

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
def assignment() -> None:
    """RBAC assignment commands."""


@assignment.command()
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
def search(
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
        registry = await create_v2_registry(load_v2_config())
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


@assignment.command()
@click.option("--user-id", required=True, help="User UUID to assign the role to.")
@click.option("--role-id", required=True, help="Role UUID to assign.")
def assign(user_id: str, role_id: str) -> None:
    """Assign a role to a user."""
    from ai.backend.common.dto.manager.v2.rbac.request import AssignRoleInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.rbac.assign_role(
                AssignRoleInput(user_id=UUID(user_id), role_id=UUID(role_id)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@assignment.command()
@click.option("--user-id", required=True, help="User UUID to revoke the role from.")
@click.option("--role-id", required=True, help="Role UUID to revoke.")
def revoke(user_id: str, role_id: str) -> None:
    """Revoke a role from a user."""
    from ai.backend.common.dto.manager.v2.rbac.request import RevokeRoleInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.rbac.revoke_role(
                RevokeRoleInput(user_id=UUID(user_id), role_id=UUID(role_id)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
