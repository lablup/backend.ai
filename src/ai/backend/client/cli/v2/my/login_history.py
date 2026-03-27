"""CLI commands for self-service login history operations."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group(name="login-history")
def login_history() -> None:
    """My login history commands."""


@login_history.command()
@click.option("--first", default=None, type=int, help="Cursor-based: return first N items.")
@click.option("--after", default=None, type=str, help="Cursor-based: return items after cursor.")
@click.option("--last", default=None, type=int, help="Cursor-based: return last N items.")
@click.option("--before", default=None, type=str, help="Cursor-based: return items before cursor.")
@click.option("--limit", default=None, type=int, help="Maximum number of results to return.")
@click.option("--offset", default=None, type=int, help="Number of results to skip.")
@click.option(
    "--result",
    type=click.Choice(
        [
            "success",
            "failed_invalid_credentials",
            "failed_user_inactive",
            "failed_blocked",
            "failed_password_expired",
            "failed_rejected_by_hook",
            "failed_session_already_exists",
        ],
        case_sensitive=False,
    ),
    default=None,
    help="Filter by login attempt result.",
)
@click.option(
    "--order-by",
    multiple=True,
    help=(
        "Order by field:direction (e.g., created_at:desc). Fields: created_at, result, domain_name."
    ),
)
def search(
    first: int | None,
    after: str | None,
    last: int | None,
    before: str | None,
    limit: int | None,
    offset: int | None,
    result: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search my login history."""
    from ai.backend.common.dto.manager.v2.login_history.request import (
        LoginHistoryFilter,
        LoginHistoryOrder,
        LoginHistoryResultFilter,
        MySearchLoginHistoryInput,
    )
    from ai.backend.common.dto.manager.v2.login_history.types import (
        LoginAttemptResult,
        LoginHistoryOrderField,
    )

    # Build filter only if any filter option is provided
    filter_dto: LoginHistoryFilter | None = None
    if result is not None:
        filter_dto = LoginHistoryFilter(
            result=LoginHistoryResultFilter(equals=LoginAttemptResult(result)),
        )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, LoginHistoryOrderField, LoginHistoryOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result_payload = await registry.login_history.my_search(
                MySearchLoginHistoryInput(
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
            print_result(result_payload)
        finally:
            await registry.close()

    asyncio.run(_run())
