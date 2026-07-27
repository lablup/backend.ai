"""CLI commands for replica-group scheduling history."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)

if TYPE_CHECKING:
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        ReplicaGroupHistoryFilter,
    )

# Shared result choices for scheduling history filters
RESULT_CHOICES = click.Choice(
    ["SUCCESS", "FAILURE", "STALE", "NEED_RETRY", "EXPIRED", "GIVE_UP", "SKIPPED"],
    case_sensitive=False,
)

CATEGORY_CHOICES = click.Choice(["lifecycle", "scaling"], case_sensitive=False)

ORDER_BY_HELP = (
    "Order by field:direction (e.g., created_at:desc). Fields: created_at, updated_at, phase,"
    " from_status, to_status, result, attempts."
)


def build_replica_group_history_filter(
    category: tuple[str, ...],
    phase: str | None,
    from_status: tuple[str, ...],
    to_status: tuple[str, ...],
    result: str | None,
    error_code: str | None,
    message: str | None,
) -> ReplicaGroupHistoryFilter | None:
    """Build a ReplicaGroupHistoryFilter from explicit CLI options.

    Returns None if no filter options were provided.
    """
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        ReplicaGroupHistoryFilter,
        SchedulingResultFilter,
    )
    from ai.backend.common.dto.manager.v2.scheduling_history.types import (
        ReplicaGroupHistoryCategoryType,
        SchedulingResultType,
    )

    has_any = any(opt is not None for opt in (phase, result, error_code, message))
    if not has_any and not category and not from_status and not to_status:
        return None

    return ReplicaGroupHistoryFilter(
        category=(
            [ReplicaGroupHistoryCategoryType(c.lower()) for c in category] if category else None
        ),
        phase=StringFilter(contains=phase) if phase is not None else None,
        from_status=list(from_status) if from_status else None,
        to_status=list(to_status) if to_status else None,
        result=(
            SchedulingResultFilter(equals=SchedulingResultType(result))
            if result is not None
            else None
        ),
        error_code=StringFilter(contains=error_code) if error_code is not None else None,
        message=StringFilter(contains=message) if message is not None else None,
    )


@click.group(name="replica-group")
def replica_group() -> None:
    """Replica-group scheduling history commands."""


@replica_group.command(name="search-scoped")
@click.argument("deployment_id", type=str)
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
def search_scoped(
    deployment_id: str,
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
    """Search replica-group scheduling history scoped to DEPLOYMENT_ID.

    A replica group is not an RBAC scope of its own, so the scope is the owning
    deployment: this returns the history of every replica group under it.
    """
    from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        ReplicaGroupHistoryOrder,
        ScopedSearchReplicaGroupHistoriesInput,
    )
    from ai.backend.common.dto.manager.v2.scheduling_history.types import (
        ReplicaGroupHistoryOrderField,
        ReplicaGroupHistoryScopeDTO,
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
            result_data = await registry.scheduling_history.replica_group_scoped_search(
                ScopedSearchReplicaGroupHistoriesInput(
                    scope=ReplicaGroupHistoryScopeDTO(
                        deployment=[UUIDScope(value=UUID(deployment_id))],
                    ),
                    filter=history_filter,
                    order=orders,
                    limit=limit,
                    offset=offset,
                )
            )
            print_result(result_data)
        finally:
            await registry.close()

    asyncio.run(_run())
