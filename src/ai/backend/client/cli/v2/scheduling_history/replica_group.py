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
_RESULT_CHOICES = click.Choice(
    ["SUCCESS", "FAILURE", "STALE", "NEED_RETRY", "EXPIRED", "GIVE_UP", "SKIPPED"],
    case_sensitive=False,
)

_CATEGORY_CHOICES = click.Choice(["lifecycle", "scaling"], case_sensitive=False)

_ORDER_BY_HELP = (
    "Order by field:direction (e.g., created_at:desc). Fields: created_at, updated_at, phase,"
    " from_status, to_status, result, attempts."
)


def _build_replica_group_history_filter(
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
@click.option(
    "--deployment-id",
    type=str,
    default=None,
    help="Scope to a deployment; covers every replica group under it.",
)
@click.option(
    "--replica-group-id",
    type=str,
    default=None,
    help="Scope to a single replica group.",
)
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--category",
    type=_CATEGORY_CHOICES,
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
@click.option("--result", type=_RESULT_CHOICES, default=None, help="Filter by scheduling result.")
@click.option("--error-code", type=str, default=None, help="Filter by error code (contains).")
@click.option("--message", type=str, default=None, help="Filter by message (contains).")
@click.option("--order-by", multiple=True, help=_ORDER_BY_HELP)
def search_scoped(
    deployment_id: str | None,
    replica_group_id: str | None,
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
    """Search replica-group scheduling history under a deployment or replica group.

    The scope has two axes, so it is given as options rather than a positional
    argument; give exactly one of them.
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

    if (deployment_id is None) == (replica_group_id is None):
        raise click.UsageError("Give exactly one of --deployment-id or --replica-group-id.")

    history_filter = _build_replica_group_history_filter(
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
            result_data = await registry.scheduling_history.scoped_search_replica_group_history(
                ScopedSearchReplicaGroupHistoriesInput(
                    scope=ReplicaGroupHistoryScopeDTO(
                        deployment=(
                            [UUIDScope(value=UUID(deployment_id))]
                            if deployment_id is not None
                            else None
                        ),
                        replica_group=(
                            [UUIDScope(value=UUID(replica_group_id))]
                            if replica_group_id is not None
                            else None
                        ),
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


@replica_group.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--category",
    type=_CATEGORY_CHOICES,
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
@click.option("--result", type=_RESULT_CHOICES, default=None, help="Filter by scheduling result.")
@click.option("--error-code", type=str, default=None, help="Filter by error code (contains).")
@click.option("--message", type=str, default=None, help="Filter by message (contains).")
@click.option("--order-by", multiple=True, help=_ORDER_BY_HELP)
def search(
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
    """Search replica-group scheduling histories (superadmin only)."""
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        AdminSearchReplicaGroupHistoriesInput,
        ReplicaGroupHistoryOrder,
    )
    from ai.backend.common.dto.manager.v2.scheduling_history.types import (
        ReplicaGroupHistoryOrderField,
    )

    history_filter = _build_replica_group_history_filter(
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
