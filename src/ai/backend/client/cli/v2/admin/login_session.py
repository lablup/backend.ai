"""Admin CLI commands for login session management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group(name="login-session")
def login_session() -> None:
    """Login session admin commands."""


@login_session.command()
@click.option("--first", default=None, type=int, help="Cursor-based: return first N items.")
@click.option("--after", default=None, type=str, help="Cursor-based: return items after cursor.")
@click.option("--last", default=None, type=int, help="Cursor-based: return last N items.")
@click.option("--before", default=None, type=str, help="Cursor-based: return items before cursor.")
@click.option("--limit", default=None, type=int, help="Maximum number of results to return.")
@click.option("--offset", default=None, type=int, help="Number of results to skip.")
@click.option(
    "--status",
    type=click.Choice(["active", "invalidated", "revoked"], case_sensitive=False),
    default=None,
    help="Filter by login session status.",
)
@click.option(
    "--access-key-contains",
    default=None,
    type=str,
    help="Filter sessions whose access key contains this substring.",
)
@click.option(
    "--created-after",
    default=None,
    type=str,
    help="Filter sessions created after this ISO 8601 datetime.",
)
@click.option(
    "--order-by",
    multiple=True,
    help=(
        "Order by field:direction (e.g., created_at:desc). "
        "Fields: created_at, status, last_accessed_at."
    ),
)
def search(
    first: int | None,
    after: str | None,
    last: int | None,
    before: str | None,
    limit: int | None,
    offset: int | None,
    status: str | None,
    access_key_contains: str | None,
    created_after: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search all login sessions (superadmin only)."""
    from ai.backend.common.dto.manager.v2.login_session.request import (
        AdminSearchLoginSessionsInput,
        LoginSessionFilter,
        LoginSessionOrder,
        LoginSessionStatusFilter,
    )
    from ai.backend.common.dto.manager.v2.login_session.types import (
        LoginSessionOrderField,
        LoginSessionStatus,
    )

    # Build filter only if any filter option is provided
    filter_dto: LoginSessionFilter | None = None
    if any(opt is not None for opt in (status, access_key_contains, created_after)):
        from datetime import datetime

        from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter

        filter_dto = LoginSessionFilter(
            status=(
                LoginSessionStatusFilter(equals=LoginSessionStatus(status))
                if status is not None
                else None
            ),
            access_key=(
                StringFilter(contains=access_key_contains)
                if access_key_contains is not None
                else None
            ),
            created_at=(
                DateTimeFilter(after=datetime.fromisoformat(created_after))
                if created_after is not None
                else None
            ),
        )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, LoginSessionOrderField, LoginSessionOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.login_session.admin_search(
                AdminSearchLoginSessionsInput(
                    filter=filter_dto,
                    order=orders,
                    first=first,
                    after=after,
                    last=last,
                    before=before,
                    limit=limit,
                    offset=offset,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@login_session.command()
@click.argument("session_id")
def revoke(session_id: str) -> None:
    """Revoke a login session by session ID (superadmin only)."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.login_session.request import (
        AdminRevokeLoginSessionInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.login_session.admin_revoke(
                AdminRevokeLoginSessionInput(session_id=UUID(session_id)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
