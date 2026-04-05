"""User-facing CLI commands for the deployment v2 REST API."""

from __future__ import annotations

import asyncio
import json
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config, print_result


@click.group()
def deployment() -> None:
    """Deployment management commands."""


@deployment.command(name="project-search")
@click.argument("project_id", type=str)
@click.option("--limit", type=int, default=20, help="Maximum items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., name:asc, created_at:desc).",
)
@click.option("--name-contains", default=None, type=str, help="Filter by name (contains).")
@click.option(
    "--status",
    multiple=True,
    help="Filter by status (repeatable, e.g., --status ACTIVE --status DEGRADED).",
)
@click.option(
    "--open-to-public",
    default=None,
    type=bool,
    help="Filter by public access (true/false).",
)
def project_search(
    project_id: str,
    limit: int,
    offset: int,
    order_by: tuple[str, ...],
    name_contains: str | None,
    status: tuple[str, ...],
    open_to_public: bool | None,
) -> None:
    """Search deployments within a project."""

    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.deployment.request import (
        AdminSearchDeploymentsInput,
        DeploymentFilter,
        DeploymentOrder,
        DeploymentStatusFilter,
    )
    from ai.backend.common.dto.manager.v2.deployment.types import DeploymentOrderField

    filter_dto: DeploymentFilter | None = None
    if name_contains or status or open_to_public is not None:
        filter_dto = DeploymentFilter(
            name=StringFilter(contains=name_contains) if name_contains else None,
            status=DeploymentStatusFilter(in_=list(status)) if status else None,
            open_to_public=open_to_public,
        )

    orders: list[DeploymentOrder] | None = None
    if order_by:
        from ai.backend.common.dto.manager.v2.common import OrderDirection

        parsed: list[DeploymentOrder] = []
        for spec in order_by:
            parts = spec.split(":")
            field_name = parts[0]
            direction = OrderDirection(parts[1].lower()) if len(parts) > 1 else OrderDirection.DESC
            parsed.append(
                DeploymentOrder(field=DeploymentOrderField(field_name), direction=direction)
            )
        orders = parsed

    body = AdminSearchDeploymentsInput(
        filter=filter_dto,
        order=orders,
        limit=limit,
        offset=offset,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.project_search(UUID(project_id), body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@deployment.command()
@click.argument("deployment_id", type=str)
def get(deployment_id: str) -> None:
    """Get a deployment by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.get(UUID(deployment_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@deployment.command()
@click.option("--name", required=True, type=str, help="Deployment name.")
@click.option("--project-id", required=True, type=str, help="Project (group) UUID.")
@click.option("--domain-name", default="default", type=str, help="Domain name.")
@click.option("--desired-replicas", default=0, type=int, help="Desired number of replicas.")
@click.option("--open-to-public", default=False, is_flag=True, help="Make publicly accessible.")
@click.option(
    "--strategy",
    default="ROLLING",
    type=click.Choice(["ROLLING", "BLUE_GREEN"], case_sensitive=False),
    help="Deployment strategy.",
)
@click.option(
    "--initial-revision",
    default=None,
    type=str,
    help="Initial revision as JSON string or @file path. If omitted, deployment starts without a revision.",
)
def create(
    name: str,
    project_id: str,
    domain_name: str,
    desired_replicas: int,
    open_to_public: bool,
    strategy: str,
    initial_revision: str | None,
) -> None:
    """Create a deployment."""

    from pathlib import Path

    from ai.backend.common.data.model_deployment.types import DeploymentStrategy
    from ai.backend.common.dto.manager.v2.deployment.request import (
        CreateDeploymentInput,
        CreateRevisionInputDTO,
        DeploymentStrategyInput,
        ModelDeploymentMetadataInput,
        ModelDeploymentNetworkAccessInput,
    )

    revision_dto: CreateRevisionInputDTO | None = None
    if initial_revision is not None:
        if initial_revision.startswith("@"):
            with Path(initial_revision[1:]).open() as f:
                rev_data = json.load(f)
        else:
            rev_data = json.loads(initial_revision)
        revision_dto = CreateRevisionInputDTO.model_validate(rev_data)

    body = CreateDeploymentInput(
        metadata=ModelDeploymentMetadataInput(
            project_id=project_id,
            domain_name=domain_name,
            name=name,
        ),
        network_access=ModelDeploymentNetworkAccessInput(
            open_to_public=open_to_public,
        ),
        default_deployment_strategy=DeploymentStrategyInput(
            type=DeploymentStrategy(strategy),
        ),
        desired_replica_count=desired_replicas,
        initial_revision=revision_dto,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.create(body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@deployment.command()
@click.argument("deployment_id", type=str)
@click.option("--name", default=None, type=str, help="Updated deployment name.")
@click.option("--desired-replicas", default=None, type=int, help="Desired number of replicas.")
@click.option("--open-to-public", default=None, type=bool, help="Network visibility.")
@click.option("--preferred-domain-name", default=None, type=str, help="Preferred domain name.")
def update(
    deployment_id: str,
    name: str | None,
    desired_replicas: int | None,
    open_to_public: bool | None,
    preferred_domain_name: str | None,
) -> None:
    """Update deployment metadata."""

    from ai.backend.common.dto.manager.v2.deployment.request import (
        UpdateDeploymentInput,
    )

    body = UpdateDeploymentInput(
        name=name,
        desired_replica_count=desired_replicas,
        open_to_public=open_to_public,
        preferred_domain_name=preferred_domain_name,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.update(UUID(deployment_id), body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@deployment.command()
@click.argument("deployment_id", type=str)
def delete(deployment_id: str) -> None:
    """Delete a deployment by ID."""

    async def _run() -> None:
        from ai.backend.common.dto.manager.v2.deployment.request import (
            DeleteDeploymentInput,
        )

        body = DeleteDeploymentInput(id=UUID(deployment_id))
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.delete(body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
