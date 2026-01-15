"""CLI commands for scheduling history."""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, Optional, Protocol

import click

from .extensions import pass_ctx_obj
from .types import CLIContext

if TYPE_CHECKING:
    from uuid import UUID

    from ai.backend.common.dto.manager.scheduling_history import (
        DeploymentHistoryDTO,
        RouteHistoryDTO,
        SessionHistoryDTO,
        SubStepResultDTO,
    )

    HistoryDTO = SessionHistoryDTO | DeploymentHistoryDTO | RouteHistoryDTO


class HistoryRecord(Protocol):
    """Protocol for history record types."""

    phase: str
    from_status: Optional[str]
    to_status: Optional[str]
    result: str
    error_code: Optional[str]
    message: Optional[str]
    sub_steps: list[SubStepResultDTO]
    created_at: str


def _format_local_time(utc_timestamp: str | None) -> str:
    """Convert UTC timestamp to local time string.

    Args:
        utc_timestamp: UTC timestamp string in ISO format

    Returns:
        Formatted local time string (YYYY-MM-DD HH:MM:SS)
    """
    if not utc_timestamp:
        return ""
    try:
        from datetime import UTC, datetime

        # Handle ISO format with or without timezone
        ts_str = utc_timestamp
        if ts_str.endswith("Z"):
            ts_str = ts_str[:-1] + "+00:00"
        dt = datetime.fromisoformat(ts_str)

        # If naive datetime, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)

        # Convert to local time
        local_dt = dt.astimezone()
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        # Fallback to string slice if parsing fails
        return utc_timestamp[:19]


def _render_sub_steps(sub_steps: list[Any], prefix: str, *, verbose: bool = False) -> None:
    """Render sub_steps with tree structure."""
    for k, step in enumerate(sub_steps):
        is_last_step = k == len(sub_steps) - 1
        step_prefix = f"{prefix}└─" if is_last_step else f"{prefix}├─"

        # Step result indicator with color
        is_success = step.result == "SUCCESS"
        step_icon = click.style("✓", fg="green") if is_success else click.style("✗", fg="red")
        step_name = (
            click.style(step.step, fg="green") if is_success else click.style(step.step, fg="red")
        )

        # Duration
        duration_str = ""
        if step.started_at and step.ended_at:
            try:
                from datetime import datetime

                start = datetime.fromisoformat(str(step.started_at))
                end = datetime.fromisoformat(str(step.ended_at))
                duration = (end - start).total_seconds()
                duration_str = f" ({duration:.2f}s)"
            except Exception:
                pass

        step_line = f"{step_prefix} {step_icon} {step_name}{duration_str}"

        # Add error message for failed steps
        if step.result != "SUCCESS" and step.message:
            step_msg = (
                step.message if verbose or len(step.message) <= 40 else step.message[:37] + "..."
            )
            step_line += f': "{step_msg}"'

        print(step_line)


def _render_flat_view(
    entity_type: str,
    histories: Sequence[HistoryDTO],
    get_entity_label: Callable[[Any], str],
    *,
    verbose: bool = False,
) -> None:
    """Render history records in flat chronological order.

    Args:
        entity_type: Type name (e.g., "Session", "Deployment", "Route")
        histories: List of history records (already sorted by time)
        get_entity_label: Function to get display label for entity
        verbose: If True, show full messages without truncation
    """
    if not histories:
        print(f"No {entity_type.lower()} history found")
        return

    print(f"{entity_type} History ({len(histories)} records)")
    print("│")

    for i, h in enumerate(histories):
        is_last = i == len(histories) - 1
        main_prefix = "└─" if is_last else "├─"
        detail_prefix = "   " if is_last else "│  "

        # Result indicator with color
        is_success = h.result == "SUCCESS"
        if is_success:
            result_indicator = click.style("[SUCCESS]", fg="green")
            phase_str = click.style(h.phase, fg="green")
        else:
            result_indicator = click.style("[FAILURE]", fg="red")
            phase_str = click.style(h.phase, fg="red")

        # Entity label
        entity_label = get_entity_label(h)

        # Status transition
        status_str = ""
        if h.from_status or h.to_status:
            status_str = f" ({h.from_status or '?'} → {h.to_status or '?'})"

        # Format timestamp (convert UTC to local time)
        created = _format_local_time(str(h.created_at) if h.created_at else None)

        print(
            f"{main_prefix} {result_indicator} {entity_label} | {phase_str}{status_str} @ {created}"
        )

        # Show error info if failure
        has_sub_steps = bool(h.sub_steps)
        if h.result != "SUCCESS" and (h.error_code or h.message):
            if h.error_code:
                error_text = click.style(f"Error: {h.error_code}", fg="red")
                connector = "│  " if (h.message or has_sub_steps) else "   "
                print(f"{detail_prefix}{connector}{error_text}")
            if h.message:
                msg = h.message if verbose or len(h.message) <= 60 else h.message[:57] + "..."
                connector = "│  " if has_sub_steps else "   "
                print(f"{detail_prefix}{connector}Message: {msg}")

        # Show sub_steps
        if has_sub_steps:
            _render_sub_steps(h.sub_steps, detail_prefix, verbose=verbose)

        if not is_last:
            print("│")


def _render_grouped_view(
    entity_type: str,
    histories: Sequence[HistoryDTO],
    get_entity_id: Callable[[Any], UUID],
    get_entity_label: Callable[[Any], str],
    *,
    verbose: bool = False,
) -> None:
    """Render history records grouped by entity.

    Args:
        entity_type: Type name (e.g., "Session", "Deployment", "Route")
        histories: List of history records
        get_entity_id: Function to extract entity ID from history record
        get_entity_label: Function to get display label for entity
        verbose: If True, show full messages without truncation
    """
    if not histories:
        print(f"No {entity_type.lower()} history found")
        return

    # Group by entity ID
    grouped: dict[str, list[HistoryDTO]] = {}
    entity_labels: dict[str, str] = {}
    for h in histories:
        eid = str(get_entity_id(h))
        if eid not in grouped:
            grouped[eid] = []
            entity_labels[eid] = get_entity_label(h)
        grouped[eid].append(h)

    print(f"{entity_type} History ({len(histories)} records)")
    print("│")

    entity_ids = list(grouped.keys())
    for i, entity_id in enumerate(entity_ids):
        is_last_entity = i == len(entity_ids) - 1
        entity_prefix = "└─" if is_last_entity else "├─"
        child_prefix = "   " if is_last_entity else "│  "

        print(f"{entity_prefix} {entity_labels[entity_id]}")

        entity_histories = grouped[entity_id]
        for j, h in enumerate(entity_histories):
            is_last_history = j == len(entity_histories) - 1
            history_prefix = f"{child_prefix}└─" if is_last_history else f"{child_prefix}├─"
            detail_prefix = f"{child_prefix}   " if is_last_history else f"{child_prefix}│  "

            # Result indicator with color
            is_success = h.result == "SUCCESS"
            if is_success:
                result_indicator = click.style("[SUCCESS]", fg="green")
                phase_str = click.style(h.phase, fg="green")
            else:
                result_indicator = click.style("[FAILURE]", fg="red")
                phase_str = click.style(h.phase, fg="red")

            # Status transition
            status_str = ""
            if h.from_status or h.to_status:
                status_str = f" ({h.from_status or '?'} → {h.to_status or '?'})"

            # Format timestamp (convert UTC to local time)
            created = _format_local_time(str(h.created_at) if h.created_at else None)

            print(f"{history_prefix} {result_indicator} {phase_str}{status_str} @ {created}")

            # Show error info if failure
            has_sub_steps = bool(h.sub_steps)
            if h.result != "SUCCESS" and (h.error_code or h.message):
                if h.error_code:
                    error_text = click.style(f"Error: {h.error_code}", fg="red")
                    connector = "│  " if (h.message or has_sub_steps) else "   "
                    print(f"{detail_prefix}{connector}{error_text}")
                if h.message:
                    msg = h.message if verbose or len(h.message) <= 60 else h.message[:57] + "..."
                    connector = "│  " if has_sub_steps else "   "
                    print(f"{detail_prefix}{connector}Message: {msg}")

            # Show sub_steps
            if has_sub_steps:
                _render_sub_steps(h.sub_steps, detail_prefix, verbose=verbose)

        if not is_last_entity:
            print("│")


@click.group()
def scheduling_history() -> None:
    """Scheduling history operations (superadmin only)"""


# Session scheduling history


@scheduling_history.group()
def session() -> None:
    """View session scheduling history"""


@session.command("list")
@pass_ctx_obj
@click.option("--session-id", type=str, default=None, help="Filter by session ID")
@click.option("--phase", type=str, default=None, help="Filter by phase (contains)")
@click.option(
    "--from-status",
    multiple=True,
    default=None,
    help="Filter by from_status (can specify multiple)",
)
@click.option(
    "--to-status", multiple=True, default=None, help="Filter by to_status (can specify multiple)"
)
@click.option(
    "--result",
    type=click.Choice(["SUCCESS", "FAILURE", "STALE"]),
    default=None,
    help="Filter by scheduling result",
)
@click.option("--error-code", type=str, default=None, help="Filter by error code")
@click.option("--message", type=str, default=None, help="Filter by message (contains)")
@click.option("--limit", type=int, default=20, help="Maximum number of records to return")
@click.option("--offset", type=int, default=0, help="Offset for pagination")
@click.option(
    "--order-by",
    type=click.Choice(["created_at", "updated_at"]),
    default="created_at",
    help="Order by field",
)
@click.option(
    "--order",
    type=click.Choice(["ASC", "DESC"]),
    default="DESC",
    help="Order direction (default: DESC to get latest records)",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--group", "group_by_entity", is_flag=True, help="Group by session ID")
@click.option("-v", "--verbose", is_flag=True, help="Show full messages without truncation")
def list_session_history_cmd(
    ctx: CLIContext,
    session_id: Optional[str],
    phase: Optional[str],
    from_status: tuple[str, ...],
    to_status: tuple[str, ...],
    result: Optional[str],
    error_code: Optional[str],
    message: Optional[str],
    limit: int,
    offset: int,
    order_by: str,
    order: str,
    as_json: bool,
    group_by_entity: bool,
    verbose: bool,
) -> None:
    """
    List session scheduling history records.
    """
    import json
    from uuid import UUID

    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session
    from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
    from ai.backend.common.dto.manager.scheduling_history import (
        OrderDirection,
        SchedulingResultType,
        SearchSessionHistoryRequest,
        SessionHistoryFilter,
        SessionHistoryOrder,
        SessionHistoryOrderField,
    )

    with Session() as api_session:
        try:
            # Build filter if any filter options are provided
            has_filter = any([
                session_id,
                phase,
                from_status,
                to_status,
                result,
                error_code,
                message,
            ])
            filter_cond = None
            if has_filter:
                filter_cond = SessionHistoryFilter(
                    session_id=UUIDFilter(equals=UUID(session_id)) if session_id else None,
                    phase=StringFilter(contains=phase) if phase else None,
                    from_status=list(from_status) if from_status else None,
                    to_status=list(to_status) if to_status else None,
                    result=[SchedulingResultType(result)] if result else None,
                    error_code=StringFilter(contains=error_code) if error_code else None,
                    message=StringFilter(contains=message) if message else None,
                )

            order_spec = SessionHistoryOrder(
                field=SessionHistoryOrderField(order_by),
                direction=OrderDirection(order.lower()),
            )

            request = SearchSessionHistoryRequest(
                filter=filter_cond,
                order=[order_spec],
                limit=limit,
                offset=offset,
            )
            response = api_session.SchedulingHistory.list_session_history(request)

            # Reverse for display when DESC (newest at bottom for readability)
            display_items = (
                list(reversed(response.items)) if order == "DESC" else list(response.items)
            )

            if as_json:
                print(
                    json.dumps(
                        [h.model_dump(mode="json") for h in response.items],
                        indent=2,
                        default=str,
                    )
                )
            elif group_by_entity:
                _render_grouped_view(
                    "Session",
                    display_items,
                    lambda h: h.session_id,
                    lambda h: f"Session: {h.session_id}",
                    verbose=verbose,
                )
            else:
                _render_flat_view(
                    "Session",
                    display_items,
                    lambda h: f"Session: {h.session_id}",
                    verbose=verbose,
                )
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


# Deployment history


@scheduling_history.group()
def deployment() -> None:
    """View deployment scheduling history"""


@deployment.command("list")
@pass_ctx_obj
@click.option("--deployment-id", type=str, default=None, help="Filter by deployment ID")
@click.option("--phase", type=str, default=None, help="Filter by phase (contains)")
@click.option(
    "--from-status",
    multiple=True,
    default=None,
    help="Filter by from_status (can specify multiple)",
)
@click.option(
    "--to-status", multiple=True, default=None, help="Filter by to_status (can specify multiple)"
)
@click.option(
    "--result",
    type=click.Choice(["SUCCESS", "FAILURE", "STALE"]),
    default=None,
    help="Filter by scheduling result",
)
@click.option("--error-code", type=str, default=None, help="Filter by error code")
@click.option("--message", type=str, default=None, help="Filter by message (contains)")
@click.option("--limit", type=int, default=20, help="Maximum number of records to return")
@click.option("--offset", type=int, default=0, help="Offset for pagination")
@click.option(
    "--order-by",
    type=click.Choice(["created_at", "updated_at"]),
    default="created_at",
    help="Order by field",
)
@click.option(
    "--order",
    type=click.Choice(["ASC", "DESC"]),
    default="DESC",
    help="Order direction (default: DESC to get latest records)",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--group", "group_by_entity", is_flag=True, help="Group by deployment ID")
@click.option("-v", "--verbose", is_flag=True, help="Show full messages without truncation")
def list_deployment_history_cmd(
    ctx: CLIContext,
    deployment_id: Optional[str],
    phase: Optional[str],
    from_status: tuple[str, ...],
    to_status: tuple[str, ...],
    result: Optional[str],
    error_code: Optional[str],
    message: Optional[str],
    limit: int,
    offset: int,
    order_by: str,
    order: str,
    as_json: bool,
    group_by_entity: bool,
    verbose: bool,
) -> None:
    """
    List deployment scheduling history records.
    """
    import json
    from uuid import UUID

    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session
    from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
    from ai.backend.common.dto.manager.scheduling_history import (
        DeploymentHistoryFilter,
        DeploymentHistoryOrder,
        DeploymentHistoryOrderField,
        OrderDirection,
        SchedulingResultType,
        SearchDeploymentHistoryRequest,
    )

    with Session() as api_session:
        try:
            # Build filter if any filter options are provided
            has_filter = any([
                deployment_id,
                phase,
                from_status,
                to_status,
                result,
                error_code,
                message,
            ])
            filter_cond = None
            if has_filter:
                filter_cond = DeploymentHistoryFilter(
                    deployment_id=UUIDFilter(equals=UUID(deployment_id)) if deployment_id else None,
                    phase=StringFilter(contains=phase) if phase else None,
                    from_status=list(from_status) if from_status else None,
                    to_status=list(to_status) if to_status else None,
                    result=[SchedulingResultType(result)] if result else None,
                    error_code=StringFilter(contains=error_code) if error_code else None,
                    message=StringFilter(contains=message) if message else None,
                )

            order_spec = DeploymentHistoryOrder(
                field=DeploymentHistoryOrderField(order_by),
                direction=OrderDirection(order.lower()),
            )

            request = SearchDeploymentHistoryRequest(
                filter=filter_cond,
                order=[order_spec],
                limit=limit,
                offset=offset,
            )
            response = api_session.SchedulingHistory.list_deployment_history(request)

            # Reverse for display when DESC (newest at bottom for readability)
            display_items = (
                list(reversed(response.items)) if order == "DESC" else list(response.items)
            )

            if as_json:
                print(
                    json.dumps(
                        [h.model_dump(mode="json") for h in response.items],
                        indent=2,
                        default=str,
                    )
                )
            elif group_by_entity:
                _render_grouped_view(
                    "Deployment",
                    display_items,
                    lambda h: h.deployment_id,
                    lambda h: f"Deployment: {h.deployment_id}",
                    verbose=verbose,
                )
            else:
                _render_flat_view(
                    "Deployment",
                    display_items,
                    lambda h: f"Deployment: {h.deployment_id}",
                    verbose=verbose,
                )
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


# Route history


@scheduling_history.group()
def route() -> None:
    """View route scheduling history"""


@route.command("list")
@pass_ctx_obj
@click.option("--route-id", type=str, default=None, help="Filter by route ID")
@click.option("--deployment-id", type=str, default=None, help="Filter by deployment ID")
@click.option("--phase", type=str, default=None, help="Filter by phase (contains)")
@click.option(
    "--from-status",
    multiple=True,
    default=None,
    help="Filter by from_status (can specify multiple)",
)
@click.option(
    "--to-status", multiple=True, default=None, help="Filter by to_status (can specify multiple)"
)
@click.option(
    "--result",
    type=click.Choice(["SUCCESS", "FAILURE", "STALE"]),
    default=None,
    help="Filter by scheduling result",
)
@click.option("--error-code", type=str, default=None, help="Filter by error code")
@click.option("--message", type=str, default=None, help="Filter by message (contains)")
@click.option("--limit", type=int, default=20, help="Maximum number of records to return")
@click.option("--offset", type=int, default=0, help="Offset for pagination")
@click.option(
    "--order-by",
    type=click.Choice(["created_at", "updated_at"]),
    default="created_at",
    help="Order by field",
)
@click.option(
    "--order",
    type=click.Choice(["ASC", "DESC"]),
    default="DESC",
    help="Order direction (default: DESC to get latest records)",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--group", "group_by_entity", is_flag=True, help="Group by route ID")
@click.option("-v", "--verbose", is_flag=True, help="Show full messages without truncation")
def list_route_history_cmd(
    ctx: CLIContext,
    route_id: Optional[str],
    deployment_id: Optional[str],
    phase: Optional[str],
    from_status: tuple[str, ...],
    to_status: tuple[str, ...],
    result: Optional[str],
    error_code: Optional[str],
    message: Optional[str],
    limit: int,
    offset: int,
    order_by: str,
    order: str,
    as_json: bool,
    group_by_entity: bool,
    verbose: bool,
) -> None:
    """
    List route scheduling history records.
    """
    import json
    from uuid import UUID

    from ai.backend.cli.types import ExitCode
    from ai.backend.client.session import Session
    from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
    from ai.backend.common.dto.manager.scheduling_history import (
        OrderDirection,
        RouteHistoryFilter,
        RouteHistoryOrder,
        RouteHistoryOrderField,
        SchedulingResultType,
        SearchRouteHistoryRequest,
    )

    with Session() as api_session:
        try:
            # Build filter if any filter options are provided
            has_filter = any([
                route_id,
                deployment_id,
                phase,
                from_status,
                to_status,
                result,
                error_code,
                message,
            ])
            filter_cond = None
            if has_filter:
                filter_cond = RouteHistoryFilter(
                    route_id=UUIDFilter(equals=UUID(route_id)) if route_id else None,
                    deployment_id=UUIDFilter(equals=UUID(deployment_id)) if deployment_id else None,
                    phase=StringFilter(contains=phase) if phase else None,
                    from_status=list(from_status) if from_status else None,
                    to_status=list(to_status) if to_status else None,
                    result=[SchedulingResultType(result)] if result else None,
                    error_code=StringFilter(contains=error_code) if error_code else None,
                    message=StringFilter(contains=message) if message else None,
                )

            order_spec = RouteHistoryOrder(
                field=RouteHistoryOrderField(order_by),
                direction=OrderDirection(order.lower()),
            )

            request = SearchRouteHistoryRequest(
                filter=filter_cond,
                order=[order_spec],
                limit=limit,
                offset=offset,
            )
            response = api_session.SchedulingHistory.list_route_history(request)

            # Reverse for display when DESC (newest at bottom for readability)
            display_items = (
                list(reversed(response.items)) if order == "DESC" else list(response.items)
            )

            def get_route_label(h: Any) -> str:
                return f"Route: {h.route_id} (Deployment: {h.deployment_id})"

            if as_json:
                print(
                    json.dumps(
                        [h.model_dump(mode="json") for h in response.items],
                        indent=2,
                        default=str,
                    )
                )
            elif group_by_entity:
                _render_grouped_view(
                    "Route",
                    display_items,
                    lambda h: h.route_id,
                    get_route_label,
                    verbose=verbose,
                )
            else:
                _render_flat_view(
                    "Route",
                    display_items,
                    get_route_label,
                    verbose=verbose,
                )
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)
