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
