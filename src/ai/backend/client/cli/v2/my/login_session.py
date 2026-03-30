"""CLI commands for self-service login session operations."""

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
    """My login session commands."""


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
    order_by: tuple[str, ...],
) -> None:
    """Search my login sessions."""
    from ai.backend.common.dto.manager.v2.login_session.request import (
        LoginSessionFilter,
        LoginSessionOrder,
        LoginSessionStatusFilter,
        MySearchLoginSessionsInput,
    )
    from ai.backend.common.dto.manager.v2.login_session.types import (
        LoginSessionOrderField,
        LoginSessionStatus,
    )

    # Build filter only if any filter option is provided
    filter_dto: LoginSessionFilter | None = None
    if status is not None:
        filter_dto = LoginSessionFilter(
            status=LoginSessionStatusFilter(equals=LoginSessionStatus(status)),
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
            result = await registry.login_session.my_search(
                MySearchLoginSessionsInput(
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
    """Revoke my login session by session ID."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.login_session.request import MyRevokeLoginSessionInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.login_session.my_revoke(
                MyRevokeLoginSessionInput(session_id=UUID(session_id)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
