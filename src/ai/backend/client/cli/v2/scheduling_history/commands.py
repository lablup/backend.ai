"""CLI commands for scheduling history management."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from uuid import UUID

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2.helpers import create_v2_registry, parse_order_options, print_result

if TYPE_CHECKING:
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        DeploymentHistoryFilter,
        RouteHistoryFilter,
        SessionHistoryFilter,
    )

# Shared result choices for scheduling history filters
_RESULT_CHOICES = click.Choice(
    ["SUCCESS", "FAILURE", "STALE", "NEED_RETRY", "EXPIRED", "GIVE_UP", "SKIPPED"],
    case_sensitive=False,
)


def _build_session_history_filter(
    session_id: str | None,
    phase: str | None,
    from_status: tuple[str, ...],
    to_status: tuple[str, ...],
    result: str | None,
    error_code: str | None,
    message: str | None,
) -> SessionHistoryFilter | None:
    """Build a SessionHistoryFilter from explicit CLI options.

    Returns None if no filter options were provided.
    """
    from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        SchedulingResultFilter,
        SessionHistoryFilter,
    )
    from ai.backend.common.dto.manager.v2.scheduling_history.types import SchedulingResultType

    has_any = any(opt is not None for opt in (session_id, phase, result, error_code, message))
    if not has_any and not from_status and not to_status:
        return None

    return SessionHistoryFilter(
        session_id=UUIDFilter(equals=UUID(session_id)) if session_id is not None else None,
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


def _build_route_history_filter(
    route_id: str | None,
    deployment_id: str | None,
    phase: str | None,
    from_status: tuple[str, ...],
    to_status: tuple[str, ...],
    result: str | None,
    error_code: str | None,
    message: str | None,
) -> RouteHistoryFilter | None:
    """Build a RouteHistoryFilter from explicit CLI options.

    Returns None if no filter options were provided.
    """
    from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        RouteHistoryFilter,
        SchedulingResultFilter,
    )
    from ai.backend.common.dto.manager.v2.scheduling_history.types import SchedulingResultType

    has_any = any(
        opt is not None for opt in (route_id, deployment_id, phase, result, error_code, message)
    )
    if not has_any and not from_status and not to_status:
        return None

    return RouteHistoryFilter(
        route_id=UUIDFilter(equals=UUID(route_id)) if route_id is not None else None,
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
def scheduling_history() -> None:
    """Scheduling history commands."""


# ========== Session History ==========


@scheduling_history.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option("--session-id", type=str, default=None, help="Filter by session ID (UUID).")
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
@pass_ctx_obj
def search_sessions(
    ctx: CLIContext,
    limit: int | None,
    offset: int | None,
    session_id: str | None,
    phase: str | None,
    from_status: tuple[str, ...],
    to_status: tuple[str, ...],
    result: str | None,
    error_code: str | None,
    message: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search session scheduling histories."""
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        AdminSearchSessionHistoriesInput,
        SessionHistoryOrder,
    )
    from ai.backend.common.dto.manager.v2.scheduling_history.types import SessionHistoryOrderField

    # Build filter from explicit CLI options
    history_filter = _build_session_history_filter(
        session_id, phase, from_status, to_status, result, error_code, message
    )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, SessionHistoryOrderField, SessionHistoryOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result_data = await registry.scheduling_history.search_session_history(
                AdminSearchSessionHistoriesInput(
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


@scheduling_history.command()
@click.argument("session_id", type=str)
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
@pass_ctx_obj
def search_session(
    ctx: CLIContext,
    session_id: str,
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
    """Search scheduling history for a specific session."""
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        AdminSearchSessionHistoriesInput,
        SessionHistoryOrder,
    )
    from ai.backend.common.dto.manager.v2.scheduling_history.types import SessionHistoryOrderField

    # Build filter from explicit CLI options (session_id is already scoped by argument)
    history_filter = _build_session_history_filter(
        None, phase, from_status, to_status, result, error_code, message
    )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, SessionHistoryOrderField, SessionHistoryOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result_data = await registry.scheduling_history.session_scoped_search(
                UUID(session_id),
                AdminSearchSessionHistoriesInput(
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


# ========== Deployment History ==========


@scheduling_history.command()
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
@pass_ctx_obj
def search_deployments(
    ctx: CLIContext,
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
        registry = await create_v2_registry(ctx)
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


@scheduling_history.command()
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
@pass_ctx_obj
def search_deployment(
    ctx: CLIContext,
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
        registry = await create_v2_registry(ctx)
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


# ========== Route History ==========


@scheduling_history.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option("--route-id", type=str, default=None, help="Filter by route ID (UUID).")
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
@pass_ctx_obj
def search_routes(
    ctx: CLIContext,
    limit: int | None,
    offset: int | None,
    route_id: str | None,
    deployment_id: str | None,
    phase: str | None,
    from_status: tuple[str, ...],
    to_status: tuple[str, ...],
    result: str | None,
    error_code: str | None,
    message: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search route scheduling histories."""
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        AdminSearchRouteHistoriesInput,
        RouteHistoryOrder,
    )
    from ai.backend.common.dto.manager.v2.scheduling_history.types import RouteHistoryOrderField

    # Build filter from explicit CLI options
    history_filter = _build_route_history_filter(
        route_id,
        deployment_id,
        phase,
        from_status,
        to_status,
        result,
        error_code,
        message,
    )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, RouteHistoryOrderField, RouteHistoryOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result_data = await registry.scheduling_history.search_route_history(
                AdminSearchRouteHistoriesInput(
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


@scheduling_history.command()
@click.argument("route_id", type=str)
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
@pass_ctx_obj
def search_route(
    ctx: CLIContext,
    route_id: str,
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
    """Search scheduling history for a specific route."""
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        AdminSearchRouteHistoriesInput,
        RouteHistoryOrder,
    )
    from ai.backend.common.dto.manager.v2.scheduling_history.types import RouteHistoryOrderField

    # Build filter from explicit CLI options (route_id is already scoped by argument)
    history_filter = _build_route_history_filter(
        None,
        deployment_id,
        phase,
        from_status,
        to_status,
        result,
        error_code,
        message,
    )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, RouteHistoryOrderField, RouteHistoryOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result_data = await registry.scheduling_history.route_scoped_search(
                UUID(route_id),
                AdminSearchRouteHistoriesInput(
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
