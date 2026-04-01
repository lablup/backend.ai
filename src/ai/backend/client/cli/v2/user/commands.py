"""CLI commands for the v2 user resource."""

from __future__ import annotations

import asyncio
import json
import sys
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group()
def user() -> None:
    """User commands."""


@user.command()
@click.argument("user_id", type=click.UUID)
def get(user_id: UUID) -> None:
    """Get a user by UUID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.user.get(user_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@user.command()
@click.argument("body", type=str)
def create(body: str) -> None:
    """Create a new user (superadmin only).

    BODY is a JSON string with user creation fields.
    """
    from ai.backend.common.dto.manager.v2.user.request import CreateUserInput

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.user.create(CreateUserInput(**data))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@user.command()
@click.argument("user_id", type=click.UUID)
@click.argument("body", type=str)
def update(user_id: UUID, body: str) -> None:
    """Update a user by UUID (superadmin only).

    BODY is a JSON string with fields to update.
    """
    from ai.backend.common.dto.manager.v2.user.request import UpdateUserInput

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.user.update(user_id, UpdateUserInput(**data))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@user.command()
@click.argument("user_id", type=click.UUID)
def delete(user_id: UUID) -> None:
    """Soft-delete a user by UUID (superadmin only)."""
    from ai.backend.common.dto.manager.v2.user.request import DeleteUserInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.user.delete(DeleteUserInput(user_id=user_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@user.command()
@click.option("--limit", default=20, help="Maximum number of results to return.")
@click.option("--offset", default=0, help="Number of results to skip.")
@click.option(
    "--scope-domain",
    default=None,
    type=str,
    help="Search users within a specific domain (by domain name).",
)
@click.option(
    "--scope-project",
    default=None,
    type=click.UUID,
    help="Search users within a specific project (by project UUID).",
)
@click.option(
    "--scope-role",
    default=None,
    type=click.UUID,
    help="Search users with a specific role (by role UUID).",
)
@click.option(
    "--username-contains",
    default=None,
    type=str,
    help="Filter users whose username contains this substring.",
)
@click.option(
    "--email-contains",
    default=None,
    type=str,
    help="Filter users whose email contains this substring.",
)
@click.option(
    "--status",
    default=None,
    type=click.Choice(
        ["active", "inactive", "deleted", "before-verification"], case_sensitive=False
    ),
    help="Filter by user status.",
)
@click.option(
    "--role",
    default=None,
    type=click.Choice(["superadmin", "admin", "user", "monitor"], case_sensitive=False),
    help="Filter by user role.",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., username:asc, created_at:desc).",
)
def search(
    limit: int,
    offset: int,
    scope_domain: str | None,
    scope_project: UUID | None,
    scope_role: UUID | None,
    username_contains: str | None,
    email_contains: str | None,
    status: str | None,
    role: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search users with optional scope filtering.

    Use --scope-domain, --scope-project, or --scope-role to narrow the search
    to a specific domain, project, or role. Without scope options, searches
    all accessible users.
    """
    from ai.backend.common.dto.manager.v2.user.request import (
        SearchUsersRequest,
        UserFilter,
        UserOrder,
    )
    from ai.backend.common.dto.manager.v2.user.types import UserOrderField

    # Validate that at most one scope option is provided
    scope_count = sum(opt is not None for opt in (scope_domain, scope_project, scope_role))
    if scope_count > 1:
        click.echo(
            "Error: Only one of --scope-domain, --scope-project, --scope-role can be specified.",
            err=True,
        )
        sys.exit(1)

    # Build filter only if any filter option is provided
    filter_dto: UserFilter | None = None
    if any(opt is not None for opt in (username_contains, email_contains, status, role)):
        from ai.backend.common.dto.manager.query import StringFilter
        from ai.backend.common.dto.manager.v2.user.types import (
            UserRole as UserRoleEnum,
        )
        from ai.backend.common.dto.manager.v2.user.types import (
            UserRoleFilter,
            UserStatus,
            UserStatusFilter,
        )

        filter_dto = UserFilter(
            username=(
                StringFilter(contains=username_contains) if username_contains is not None else None
            ),
            email=StringFilter(contains=email_contains) if email_contains is not None else None,
            status=UserStatusFilter(equals=UserStatus(status)) if status is not None else None,
            role=UserRoleFilter(equals=UserRoleEnum(role)) if role is not None else None,
        )

    # Build order only if --order-by is provided
    orders = parse_order_options(order_by, UserOrderField, UserOrder) if order_by else None

    # Validate that a scope is specified
    if scope_domain is None and scope_project is None and scope_role is None:
        click.echo(
            "Error: At least one of --scope-domain, --scope-project, "
            "or --scope-role must be specified.",
            err=True,
        )
        sys.exit(1)

    async def _search_by_domain(domain_name: str) -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = SearchUsersRequest(
                filter=filter_dto,
                order=orders,
                limit=limit,
                offset=offset,
            )
            result = await registry.user.search_by_domain(domain_name, request)
            print_result(result)
        finally:
            await registry.close()

    async def _search_by_project(project_id: UUID) -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = SearchUsersRequest(
                filter=filter_dto,
                order=orders,
                limit=limit,
                offset=offset,
            )
            result = await registry.user.search_by_project(project_id, request)
            print_result(result)
        finally:
            await registry.close()

    async def _search_by_role(role_id: UUID) -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = SearchUsersRequest(
                filter=filter_dto,
                order=orders,
                limit=limit,
                offset=offset,
            )
            result = await registry.user.search_by_role(role_id, request)
            print_result(result)
        finally:
            await registry.close()

    if scope_domain is not None:
        asyncio.run(_search_by_domain(scope_domain))
    elif scope_project is not None:
        asyncio.run(_search_by_project(scope_project))
    elif scope_role is not None:
        asyncio.run(_search_by_role(scope_role))
