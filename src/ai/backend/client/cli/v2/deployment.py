"""CLI commands for the deployment v2 REST API."""

from __future__ import annotations

import asyncio
import json
from uuid import UUID

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2._helpers import create_v2_registry, print_result


@click.group()
def deployments() -> None:
    """Deployment management commands."""


@deployments.command()
@pass_ctx_obj
def search(ctx: CLIContext) -> None:
    """Search deployments (admin, all deployments)."""

    async def _run() -> None:
        from ai.backend.common.dto.manager.v2.deployment.request import (
            AdminSearchDeploymentsInput,
        )

        registry = await create_v2_registry(ctx)
        try:
            body = AdminSearchDeploymentsInput()
            result = await registry.deployment.admin_search(body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@deployments.command()
@click.argument("deployment_id", type=str)
@pass_ctx_obj
def get(ctx: CLIContext, deployment_id: str) -> None:
    """Get a deployment by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.deployment.get(UUID(deployment_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@deployments.command()
@click.argument("payload", type=str)
@pass_ctx_obj
def create(ctx: CLIContext, payload: str) -> None:
    """Create a deployment from a JSON payload.

    PAYLOAD is a JSON string or @file path containing the CreateDeploymentInput body.
    """

    from pathlib import Path

    from ai.backend.common.dto.manager.v2.deployment.request import (
        CreateDeploymentInput,
    )

    if payload.startswith("@"):
        with Path(payload[1:]).open() as f:
            data = json.load(f)
    else:
        data = json.loads(payload)
    body = CreateDeploymentInput.model_validate(data)

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.deployment.create(body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@deployments.command()
@click.argument("deployment_id", type=str)
@pass_ctx_obj
def delete(ctx: CLIContext, deployment_id: str) -> None:
    """Delete a deployment by ID."""

    async def _run() -> None:
        from ai.backend.common.dto.manager.v2.deployment.request import (
            DeleteDeploymentInput,
        )

        body = DeleteDeploymentInput(id=UUID(deployment_id))
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.deployment.delete(body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@deployments.command(name="revisions-search")
@click.option(
    "--deployment-id",
    type=str,
    default=None,
    help="Scope to a specific deployment ID. Omit for admin-wide search.",
)
@pass_ctx_obj
def revisions_search(ctx: CLIContext, deployment_id: str | None) -> None:
    """Search deployment revisions."""

    async def _run() -> None:
        from ai.backend.common.dto.manager.v2.deployment.request import (
            AdminSearchRevisionsInput,
        )

        body = AdminSearchRevisionsInput()
        registry = await create_v2_registry(ctx)
        try:
            if deployment_id is not None:
                result = await registry.deployment.search_revisions(UUID(deployment_id), body)
            else:
                result = await registry.deployment.admin_search_revisions(body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@deployments.command(name="replicas-search")
@click.option(
    "--deployment-id",
    type=str,
    default=None,
    help="Scope to a specific deployment ID. Omit for admin-wide search.",
)
@pass_ctx_obj
def replicas_search(ctx: CLIContext, deployment_id: str | None) -> None:
    """Search deployment replicas."""

    async def _run() -> None:
        from ai.backend.common.dto.manager.v2.deployment.request import (
            SearchReplicasInput,
        )

        body = SearchReplicasInput()
        registry = await create_v2_registry(ctx)
        try:
            if deployment_id is not None:
                result = await registry.deployment.search_replicas(UUID(deployment_id), body)
            else:
                result = await registry.deployment.admin_search_replicas(body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@deployments.command(name="policies-search")
@pass_ctx_obj
def policies_search(ctx: CLIContext) -> None:
    """Search deployment policies (superadmin only)."""

    async def _run() -> None:
        from ai.backend.common.dto.manager.v2.deployment.request import (
            SearchDeploymentPoliciesInput,
        )

        body = SearchDeploymentPoliciesInput()
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.deployment.search_deployment_policies(body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
