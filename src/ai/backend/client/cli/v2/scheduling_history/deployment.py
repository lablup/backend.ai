"""CLI commands for deployment scheduling history."""

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
    from ai.backend.common.dto.manager.v2.scheduling_history.request import DeploymentHistoryFilter

# Shared result choices for scheduling history filters
_RESULT_CHOICES = click.Choice(
    ["SUCCESS", "FAILURE", "STALE", "NEED_RETRY", "EXPIRED", "GIVE_UP", "SKIPPED"],
    case_sensitive=False,
)


def _build_deployment_history_filter(
    deployment_id: str | None,
    phase: str | None,
    from_status: tuple[str, ...],
    to_status: tuple[str, ...],
    result: str | None,
    error_code: str | None,
    message: str | None,
) -> DeploymentHistoryFilter | None:
    """Build a DeploymentHistoryFilter from explicit CLI options.

    Returns None if no filter options were provided.
    """
    from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        DeploymentHistoryFilter,
        SchedulingResultFilter,
    )
    from ai.backend.common.dto.manager.v2.scheduling_history.types import SchedulingResultType

    has_any = any(opt is not None for opt in (deployment_id, phase, result, error_code, message))
    if not has_any and not from_status and not to_status:
        return None

    return DeploymentHistoryFilter(
        deployment_id=(
            UUIDFilter(equals=UUID(deployment_id)) if deployment_id is not None else None
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


@click.group()
def deployment() -> None:
    """Deployment scheduling history commands."""


@deployment.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option("--deployment-id", type=str, default=None, help="Filter by deployment ID (UUID).")
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
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., created_at:desc). Fields: created_at, updated_at.",
)
def search(
    limit: int | None,
    offset: int | None,
    deployment_id: str | None,
    phase: str | None,
    from_status: tuple[str, ...],
    to_status: tuple[str, ...],
    result: str | None,
    error_code: str | None,
    message: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search deployment scheduling histories."""
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        AdminSearchDeploymentHistoriesInput,
        DeploymentHistoryOrder,
    )
    from ai.backend.common.dto.manager.v2.scheduling_history.types import (
        DeploymentHistoryOrderField,
    )

    # Build filter from explicit CLI options
    history_filter = _build_deployment_history_filter(
        deployment_id, phase, from_status, to_status, result, error_code, message
    )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, DeploymentHistoryOrderField, DeploymentHistoryOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result_data = await registry.scheduling_history.search_deployment_history(
                AdminSearchDeploymentHistoriesInput(
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


@deployment.command(name="search-scoped")
@click.argument("deployment_id", type=str)
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
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
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., created_at:desc). Fields: created_at, updated_at.",
)
def search_scoped(
    deployment_id: str,
    limit: int | None,
    offset: int | None,
    phase: str | None,
    from_status: tuple[str, ...],
    to_status: tuple[str, ...],
    result: str | None,
    error_code: str | None,
    message: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search scheduling history for a specific deployment."""
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        AdminSearchDeploymentHistoriesInput,
        DeploymentHistoryOrder,
    )
    from ai.backend.common.dto.manager.v2.scheduling_history.types import (
        DeploymentHistoryOrderField,
    )

    # Build filter from explicit CLI options (deployment_id is already scoped by argument)
    history_filter = _build_deployment_history_filter(
        None, phase, from_status, to_status, result, error_code, message
    )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, DeploymentHistoryOrderField, DeploymentHistoryOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result_data = await registry.scheduling_history.deployment_scoped_search(
                UUID(deployment_id),
                AdminSearchDeploymentHistoriesInput(
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
