"""Admin CLI commands for the scheduling history domain."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)
from ai.backend.client.cli.v2.scheduling_history.replica_group import (
    CATEGORY_CHOICES,
    ORDER_BY_HELP,
    RESULT_CHOICES,
    build_replica_group_history_filter,
)


@click.group()
def scheduling_history() -> None:
    """Admin scheduling history commands."""


# -- Sub-group: replica-group --


@scheduling_history.group(name="replica-group")
def replica_group() -> None:
    """Admin replica-group scheduling history commands."""


@replica_group.command(name="search")
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--category",
    type=CATEGORY_CHOICES,
    multiple=True,
    help="Filter by handler category (repeatable).",
)
@click.option("--phase", type=str, default=None, help="Filter by scheduling phase (contains).")
@click.option(
    "--from-status",
    type=str,
    multiple=True,
    help="Filter by from_status values (repeatable).",
)
@click.option(
    "--to-status",
    type=str,
    multiple=True,
    help="Filter by to_status values (repeatable).",
)
@click.option("--result", type=RESULT_CHOICES, default=None, help="Filter by scheduling result.")
@click.option("--error-code", type=str, default=None, help="Filter by error code (contains).")
@click.option("--message", type=str, default=None, help="Filter by message (contains).")
@click.option("--order-by", multiple=True, help=ORDER_BY_HELP)
def replica_group_search(
    limit: int | None,
    offset: int | None,
    category: tuple[str, ...],
    phase: str | None,
    from_status: tuple[str, ...],
    to_status: tuple[str, ...],
    result: str | None,
    error_code: str | None,
    message: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search replica-group scheduling histories across the whole system."""
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        AdminSearchReplicaGroupHistoriesInput,
        ReplicaGroupHistoryOrder,
    )
    from ai.backend.common.dto.manager.v2.scheduling_history.types import (
        ReplicaGroupHistoryOrderField,
    )

    history_filter = build_replica_group_history_filter(
        category, phase, from_status, to_status, result, error_code, message
    )

    orders = (
        parse_order_options(order_by, ReplicaGroupHistoryOrderField, ReplicaGroupHistoryOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result_data = await registry.scheduling_history.admin_search_replica_group_history(
                AdminSearchReplicaGroupHistoriesInput(
                    filter=history_filter,
                    order=orders,
                    limit=limit,
                    offset=offset,
                ),
            )
            print_result(result_data)
        finally:
            await registry.close()

    asyncio.run(_run())
