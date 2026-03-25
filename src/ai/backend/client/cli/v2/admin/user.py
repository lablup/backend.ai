"""Admin CLI commands for the v2 user resource."""

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
    """Admin user commands."""


@user.command()
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
def search(
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
        SearchUsersRequest,
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
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.user.admin_search(
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
