"""CLI commands for scheduling history."""

from __future__ import annotations

import json
import sys
from typing import Optional
from uuid import UUID

import click

from ai.backend.cli.types import ExitCode
from ai.backend.client.session import Session
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.scheduling_history import (
    DeploymentHistoryFilter,
    DeploymentHistoryOrder,
    DeploymentHistoryOrderField,
    OrderDirection,
    RouteHistoryFilter,
    RouteHistoryOrder,
    RouteHistoryOrderField,
    SchedulingResultType,
    SearchDeploymentHistoryRequest,
    SearchRouteHistoryRequest,
    SearchSessionHistoryRequest,
    SessionHistoryFilter,
    SessionHistoryOrder,
    SessionHistoryOrderField,
)

from .extensions import pass_ctx_obj
from .types import CLIContext


@click.group()
def scheduling_history():
    """Scheduling history operations (superadmin only)"""


# Session scheduling history


@scheduling_history.group()
def session():
    """View session scheduling history"""


@session.command("list")
@pass_ctx_obj
@click.option("--session-id", type=str, default=None, help="Filter by session ID")
@click.option(
    "--result",
    type=click.Choice(["SUCCESS", "FAILURE", "STALE"]),
    default=None,
    help="Filter by scheduling result",
)
@click.option("--error-code", type=str, default=None, help="Filter by error code")
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
    help="Order direction",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_session_history_cmd(
    ctx: CLIContext,
    session_id: Optional[str],
    result: Optional[str],
    error_code: Optional[str],
    limit: int,
    offset: int,
    order_by: str,
    order: str,
    as_json: bool,
) -> None:
    """
    List session scheduling history records.
    """
    with Session() as api_session:
        try:
            filter_cond = None
            if session_id or result or error_code:
                filter_cond = SessionHistoryFilter(
                    session_id=UUIDFilter(equals=UUID(session_id)) if session_id else None,
                    result=[SchedulingResultType(result)] if result else None,
                    error_code=StringFilter(equals=error_code) if error_code else None,
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

            if as_json:
                print(
                    json.dumps(
                        [h.model_dump(mode="json") for h in response.items],
                        indent=2,
                        default=str,
                    )
                )
            else:
                histories = response.items
                if not histories:
                    print("No session scheduling history found")
                    return
                print(f"Total: {response.pagination.total}")
                print()
                for history in histories:
                    print(f"ID: {history.id}")
                    print(f"Session ID: {history.session_id}")
                    print(f"Phase: {history.phase}")
                    print(f"Result: {history.result}")
                    if history.from_status or history.to_status:
                        print(f"Status: {history.from_status} -> {history.to_status}")
                    if history.error_code:
                        print(f"Error: {history.error_code}")
                    if history.message:
                        print(f"Message: {history.message}")
                    print(f"Attempts: {history.attempts}")
                    print(f"Created: {history.created_at}")
                    print("---")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


# Deployment history


@scheduling_history.group()
def deployment():
    """View deployment scheduling history"""


@deployment.command("list")
@pass_ctx_obj
@click.option("--deployment-id", type=str, default=None, help="Filter by deployment ID")
@click.option(
    "--result",
    type=click.Choice(["SUCCESS", "FAILURE", "STALE"]),
    default=None,
    help="Filter by scheduling result",
)
@click.option("--error-code", type=str, default=None, help="Filter by error code")
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
    help="Order direction",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_deployment_history_cmd(
    ctx: CLIContext,
    deployment_id: Optional[str],
    result: Optional[str],
    error_code: Optional[str],
    limit: int,
    offset: int,
    order_by: str,
    order: str,
    as_json: bool,
) -> None:
    """
    List deployment scheduling history records.
    """
    with Session() as api_session:
        try:
            filter_cond = None
            if deployment_id or result or error_code:
                filter_cond = DeploymentHistoryFilter(
                    deployment_id=UUIDFilter(equals=UUID(deployment_id)) if deployment_id else None,
                    result=[SchedulingResultType(result)] if result else None,
                    error_code=StringFilter(equals=error_code) if error_code else None,
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

            if as_json:
                print(
                    json.dumps(
                        [h.model_dump(mode="json") for h in response.items],
                        indent=2,
                        default=str,
                    )
                )
            else:
                histories = response.items
                if not histories:
                    print("No deployment history found")
                    return
                print(f"Total: {response.pagination.total}")
                print()
                for history in histories:
                    print(f"ID: {history.id}")
                    print(f"Deployment ID: {history.deployment_id}")
                    print(f"Phase: {history.phase}")
                    print(f"Result: {history.result}")
                    if history.from_status or history.to_status:
                        print(f"Status: {history.from_status} -> {history.to_status}")
                    if history.error_code:
                        print(f"Error: {history.error_code}")
                    if history.message:
                        print(f"Message: {history.message}")
                    print(f"Attempts: {history.attempts}")
                    print(f"Created: {history.created_at}")
                    print("---")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


# Route history


@scheduling_history.group()
def route():
    """View route scheduling history"""


@route.command("list")
@pass_ctx_obj
@click.option("--route-id", type=str, default=None, help="Filter by route ID")
@click.option("--deployment-id", type=str, default=None, help="Filter by deployment ID")
@click.option(
    "--result",
    type=click.Choice(["SUCCESS", "FAILURE", "STALE"]),
    default=None,
    help="Filter by scheduling result",
)
@click.option("--error-code", type=str, default=None, help="Filter by error code")
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
    help="Order direction",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_route_history_cmd(
    ctx: CLIContext,
    route_id: Optional[str],
    deployment_id: Optional[str],
    result: Optional[str],
    error_code: Optional[str],
    limit: int,
    offset: int,
    order_by: str,
    order: str,
    as_json: bool,
) -> None:
    """
    List route scheduling history records.
    """
    with Session() as api_session:
        try:
            filter_cond = None
            if route_id or deployment_id or result or error_code:
                filter_cond = RouteHistoryFilter(
                    route_id=UUIDFilter(equals=UUID(route_id)) if route_id else None,
                    deployment_id=UUIDFilter(equals=UUID(deployment_id)) if deployment_id else None,
                    result=[SchedulingResultType(result)] if result else None,
                    error_code=StringFilter(equals=error_code) if error_code else None,
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

            if as_json:
                print(
                    json.dumps(
                        [h.model_dump(mode="json") for h in response.items],
                        indent=2,
                        default=str,
                    )
                )
            else:
                histories = response.items
                if not histories:
                    print("No route history found")
                    return
                print(f"Total: {response.pagination.total}")
                print()
                for history in histories:
                    print(f"ID: {history.id}")
                    print(f"Route ID: {history.route_id}")
                    print(f"Deployment ID: {history.deployment_id}")
                    print(f"Phase: {history.phase}")
                    print(f"Result: {history.result}")
                    if history.from_status or history.to_status:
                        print(f"Status: {history.from_status} -> {history.to_status}")
                    if history.error_code:
                        print(f"Error: {history.error_code}")
                    if history.message:
                        print(f"Message: {history.message}")
                    print(f"Attempts: {history.attempts}")
                    print(f"Created: {history.created_at}")
                    print("---")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)
