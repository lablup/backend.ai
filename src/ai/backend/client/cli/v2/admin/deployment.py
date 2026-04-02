"""Admin CLI commands for the deployment domain."""

from __future__ import annotations

import asyncio
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)
from ai.backend.common.cli import LazyGroup


@click.group()
def deployment() -> None:
    """Admin deployment commands."""


@deployment.command(name="search")
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., name:asc, created_at:desc, updated_at:desc).",
)
@click.option("--name-contains", type=str, default=None, help="Filter by name (contains).")
@click.option(
    "--status",
    type=str,
    multiple=True,
    help="Filter by status (repeatable, e.g., --status ACTIVE --status DEGRADED).",
)
@click.option(
    "--open-to-public",
    type=bool,
    default=None,
    help="Filter by public access (true/false).",
)
@click.option("--tags-contains", type=str, default=None, help="Filter by tags (contains).")
@click.option(
    "--endpoint-url-contains",
    type=str,
    default=None,
    help="Filter by endpoint URL (contains).",
)
def search(
    limit: int | None,
    offset: int | None,
    order_by: tuple[str, ...],
    name_contains: str | None,
    status: tuple[str, ...],
    open_to_public: bool | None,
    tags_contains: str | None,
    endpoint_url_contains: str | None,
) -> None:
    """Search all deployments (admin)."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.deployment.request import (
        AdminSearchDeploymentsInput,
        DeploymentFilter,
        DeploymentOrder,
        DeploymentStatusFilter,
    )
    from ai.backend.common.dto.manager.v2.deployment.types import DeploymentOrderField

    # Build filter only if any filter option is provided
    filter_dto: DeploymentFilter | None = None
    if any([
        name_contains is not None,
        status,
        open_to_public is not None,
        tags_contains is not None,
        endpoint_url_contains is not None,
    ]):
        filter_dto = DeploymentFilter(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            status=(DeploymentStatusFilter(in_=list(status)) if status else None),
            open_to_public=open_to_public,
            tags=StringFilter(contains=tags_contains) if tags_contains is not None else None,
            endpoint_url=(
                StringFilter(contains=endpoint_url_contains)
                if endpoint_url_contains is not None
                else None
            ),
        )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, DeploymentOrderField, DeploymentOrder) if order_by else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.admin_search(
                AdminSearchDeploymentsInput(
                    filter=filter_dto,
                    order=orders,
                    limit=limit,
                    offset=offset,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# -- Sub-group: revision --


@deployment.group()
def revision() -> None:
    """Admin deployment revision commands."""


@revision.command(name="search")
@click.option(
    "--deployment-id",
    type=str,
    default=None,
    help="Scope to a specific deployment ID. Omit for admin-wide search.",
)
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., name:asc, created_at:desc).",
)
@click.option(
    "--name-contains", type=str, default=None, help="Filter revisions by name (contains)."
)
def revision_search(
    deployment_id: str | None,
    limit: int | None,
    offset: int | None,
    order_by: tuple[str, ...],
    name_contains: str | None,
) -> None:
    """Search deployment revisions (admin)."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.deployment.request import (
        AdminSearchRevisionsInput,
        RevisionFilter,
        RevisionOrder,
    )
    from ai.backend.common.dto.manager.v2.deployment.types import RevisionOrderField

    # Build filter only if any filter option is provided
    filter_dto: RevisionFilter | None = None
    if name_contains is not None or deployment_id is not None:
        filter_dto = RevisionFilter(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            deployment_id=UUID(deployment_id) if deployment_id is not None else None,
        )

    # Build order only if --order-by is provided
    orders = parse_order_options(order_by, RevisionOrderField, RevisionOrder) if order_by else None

    async def _run() -> None:
        body = AdminSearchRevisionsInput(
            filter=filter_dto,
            order=orders,
            limit=limit,
            offset=offset,
        )
        registry = await create_v2_registry(load_v2_config())
        try:
            if deployment_id is not None:
                result = await registry.deployment.search_revisions(UUID(deployment_id), body)
            else:
                result = await registry.deployment.admin_search_revisions(body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# -- Sub-group: replica --


@deployment.group()
def replica() -> None:
    """Admin deployment replica commands."""


@replica.command(name="search")
@click.option(
    "--deployment-id",
    type=str,
    default=None,
    help="Scope to a specific deployment ID. Omit for admin-wide search.",
)
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
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
def replica_search(
    deployment_id: str | None,
    limit: int | None,
    offset: int | None,
    order_by: tuple[str, ...],
    status_equals: str | None,
    traffic_status_equals: str | None,
) -> None:
    """Search deployment replicas (admin)."""
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

    # Build filter only if any filter option is provided
    filter_dto: ReplicaFilter | None = None
    if any([
        deployment_id is not None,
        status_equals is not None,
        traffic_status_equals is not None,
    ]):
        filter_dto = ReplicaFilter(
            deployment_id=UUID(deployment_id) if deployment_id is not None else None,
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

    # Build order only if --order-by is provided
    orders = parse_order_options(order_by, ReplicaOrderField, ReplicaOrder) if order_by else None

    async def _run() -> None:
        body = SearchReplicasInput(
            filter=filter_dto,
            order=orders,
            limit=limit,
            offset=offset,
        )
        registry = await create_v2_registry(load_v2_config())
        try:
            if deployment_id is not None:
                result = await registry.deployment.search_replicas(UUID(deployment_id), body)
            else:
                result = await registry.deployment.admin_search_replicas(body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# -- Sub-group: policy --


@deployment.group()
def policy() -> None:
    """Admin deployment policy commands."""


@policy.command(name="search")
@click.option(
    "--deployment-id",
    type=str,
    default=None,
    help="Filter policies by deployment ID.",
)
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
def policy_search(
    deployment_id: str | None,
    limit: int | None,
    offset: int | None,
) -> None:
    """Search deployment policies (superadmin only)."""
    from ai.backend.common.dto.manager.v2.deployment.request import (
        DeploymentPolicyFilter,
        SearchDeploymentPoliciesInput,
    )

    # Build filter only if deployment-id is provided
    filter_dto: DeploymentPolicyFilter | None = None
    if deployment_id is not None:
        filter_dto = DeploymentPolicyFilter(
            deployment_id=UUID(deployment_id),
        )

    async def _run() -> None:
        body = SearchDeploymentPoliciesInput(
            filter=filter_dto,
            limit=limit,
            offset=offset,
        )
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.search_deployment_policies(body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# -- Sub-group: revision-preset --


@deployment.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.admin.deployment_revision_preset:deployment_revision_preset",
    name="revision-preset",
)
def revision_preset() -> None:
    """Admin deployment revision preset commands."""
