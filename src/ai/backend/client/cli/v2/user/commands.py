"""CLI commands for the v2 user resource."""

from __future__ import annotations

import asyncio
import json
import sys
from uuid import UUID

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2.helpers import create_v2_registry, parse_order_options, print_result


@click.group()
def users() -> None:
    """User management commands."""


@users.command(name="admin-search")
@pass_ctx_obj
@click.option("--limit", default=20, help="Maximum number of results to return.")
@click.option("--offset", default=0, help="Number of results to skip.")
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
@click.option("--domain-name", default=None, type=str, help="Filter by exact domain name.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., username:asc, created_at:desc).",
)
def admin_search(
    ctx: CLIContext,
    limit: int,
    offset: int,
    username_contains: str | None,
    email_contains: str | None,
    status: str | None,
    role: str | None,
    domain_name: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search users (superadmin only)."""
    from ai.backend.common.dto.manager.v2.user.request import (
        AdminSearchUsersInput,
        UserFilter,
        UserOrder,
    )
    from ai.backend.common.dto.manager.v2.user.types import UserOrderField

    # Build filter only if any filter option is provided
    filter_dto: UserFilter | None = None
    if any(
        opt is not None for opt in (username_contains, email_contains, status, role, domain_name)
    ):
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
            domain_name=(StringFilter(equals=domain_name) if domain_name is not None else None),
        )

    # Build order only if --order-by is provided
    orders = parse_order_options(order_by, UserOrderField, UserOrder) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.user.admin_search(
                AdminSearchUsersInput(
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


@users.command()
@pass_ctx_obj
@click.argument("user_id", type=click.UUID)
def get(ctx: CLIContext, user_id: UUID) -> None:
    """Get a user by UUID."""

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.user.get(user_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@users.command()
@pass_ctx_obj
@click.argument("body", type=str)
def create(ctx: CLIContext, body: str) -> None:
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
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.user.create(CreateUserInput(**data))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@users.command()
@pass_ctx_obj
@click.argument("user_id", type=click.UUID)
@click.argument("body", type=str)
def update(ctx: CLIContext, user_id: UUID, body: str) -> None:
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
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.user.update(user_id, UpdateUserInput(**data))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@users.command()
@pass_ctx_obj
@click.argument("user_id", type=click.UUID)
def delete(ctx: CLIContext, user_id: UUID) -> None:
    """Soft-delete a user by UUID (superadmin only)."""
    from ai.backend.common.dto.manager.v2.user.request import DeleteUserInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.user.delete(DeleteUserInput(user_id=user_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@users.command(name="search-by-domain")
@pass_ctx_obj
@click.argument("domain_name")
@click.option("--limit", default=20, help="Maximum number of results to return.")
@click.option("--offset", default=0, help="Number of results to skip.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., username:asc, created_at:desc).",
)
def search_by_domain(
    ctx: CLIContext,
    domain_name: str,
    limit: int,
    offset: int,
    order_by: tuple[str, ...],
) -> None:
    """Search users within a specific domain."""
    from ai.backend.common.dto.manager.v2.user.request import SearchUsersRequest, UserOrder
    from ai.backend.common.dto.manager.v2.user.types import UserOrderField

    # Build order only if --order-by is provided
    orders = parse_order_options(order_by, UserOrderField, UserOrder) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.user.search_by_domain(
                domain_name,
                SearchUsersRequest(
                    order=orders,
                    limit=limit,
                    offset=offset,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@users.command(name="search-by-project")
@pass_ctx_obj
@click.argument("project_id", type=click.UUID)
@click.option("--limit", default=20, help="Maximum number of results to return.")
@click.option("--offset", default=0, help="Number of results to skip.")
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
def search_by_project(
    ctx: CLIContext,
    project_id: UUID,
    limit: int,
    offset: int,
    username_contains: str | None,
    email_contains: str | None,
    status: str | None,
    role: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search users within a specific project."""
    from ai.backend.common.dto.manager.v2.user.request import (
        SearchUsersRequest,
        UserFilter,
        UserOrder,
    )
    from ai.backend.common.dto.manager.v2.user.types import UserOrderField

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

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.user.search_by_project(
                project_id,
                SearchUsersRequest(
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


@users.command(name="search-by-role")
@pass_ctx_obj
@click.argument("role_id", type=click.UUID)
@click.option("--limit", default=20, help="Maximum number of results to return.")
@click.option("--offset", default=0, help="Number of results to skip.")
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
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., username:asc, created_at:desc).",
)
def search_by_role(
    ctx: CLIContext,
    role_id: UUID,
    limit: int,
    offset: int,
    username_contains: str | None,
    email_contains: str | None,
    status: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search users with a specific role."""
    from ai.backend.common.dto.manager.v2.user.request import (
        SearchUsersRequest,
        UserFilter,
        UserOrder,
    )
    from ai.backend.common.dto.manager.v2.user.types import UserOrderField

    # Build filter only if any filter option is provided
    filter_dto: UserFilter | None = None
    if any(opt is not None for opt in (username_contains, email_contains, status)):
        from ai.backend.common.dto.manager.query import StringFilter
        from ai.backend.common.dto.manager.v2.user.types import (
            UserStatus,
            UserStatusFilter,
        )

        filter_dto = UserFilter(
            username=(
                StringFilter(contains=username_contains) if username_contains is not None else None
            ),
            email=StringFilter(contains=email_contains) if email_contains is not None else None,
            status=UserStatusFilter(equals=UserStatus(status)) if status is not None else None,
        )

    # Build order only if --order-by is provided
    orders = parse_order_options(order_by, UserOrderField, UserOrder) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.user.search_by_role(
                role_id,
                SearchUsersRequest(
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
