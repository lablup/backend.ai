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
@click.argument("payload", type=str)
def create(payload: str) -> None:
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
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.create(body)
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
