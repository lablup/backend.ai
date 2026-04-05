"""User-facing CLI commands for deployment replicas."""

from __future__ import annotations

import asyncio
import sys
import uuid
from typing import Any

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


def _run_async(coro_fn: Any) -> None:
    from ai.backend.client.exceptions import BackendAPIError

    try:
        asyncio.run(coro_fn())
    except BackendAPIError as e:
        data = e.args[2] if len(e.args) > 2 else {}
        title = data.get("title", "") if isinstance(data, dict) else ""
        msg = data.get("msg", "") if isinstance(data, dict) else ""
        status = e.args[0] if e.args else "?"
        detail = title or msg or str(e)
        click.echo(f"Error ({status}): {detail}", err=True)
        sys.exit(1)


@click.group()
def replica() -> None:
    """Deployment replica commands."""


@replica.command()
@click.argument("deployment_id", type=click.UUID)
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., created_at:desc, id:asc).",
)
@click.option(
    "--status-equals",
    type=str,
    default=None,
    help="Filter replicas by exact status (e.g., HEALTHY, UNHEALTHY).",
)
@click.option(
    "--traffic-status-equals",
    type=str,
    default=None,
    help="Filter replicas by exact traffic status (e.g., ACTIVE, INACTIVE).",
)
def search(
    deployment_id: uuid.UUID,
    limit: int,
    offset: int,
    order_by: tuple[str, ...],
    status_equals: str | None,
    traffic_status_equals: str | None,
) -> None:
    """Search replicas for a deployment."""
    from ai.backend.common.data.model_deployment.types import (
        RouteStatus,
        RouteTrafficStatus,
    )
    from ai.backend.common.dto.manager.v2.deployment.request import (
        ReplicaFilter,
        ReplicaOrder,
        ReplicaStatusFilter,
        ReplicaTrafficStatusFilter,
        SearchReplicasInput,
    )
    from ai.backend.common.dto.manager.v2.deployment.types import ReplicaOrderField

    filter_dto: ReplicaFilter | None = None
    if status_equals is not None or traffic_status_equals is not None:
        filter_dto = ReplicaFilter(
            status=(
                ReplicaStatusFilter(equals=RouteStatus(status_equals))
                if status_equals is not None
                else None
            ),
            traffic_status=(
                ReplicaTrafficStatusFilter(equals=RouteTrafficStatus(traffic_status_equals))
                if traffic_status_equals is not None
                else None
            ),
        )
    orders = parse_order_options(order_by, ReplicaOrderField, ReplicaOrder) if order_by else None

    body = SearchReplicasInput(
        filter=filter_dto,
        order=orders,
        limit=limit,
        offset=offset,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.search_replicas(deployment_id, body)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)
