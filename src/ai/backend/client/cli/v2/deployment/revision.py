"""User-facing CLI commands for deployment revisions."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    print_result,
)


@click.group()
def revision() -> None:
    """Deployment revision commands."""


@revision.command()
@click.argument("deployment_id", type=str)
@click.argument("payload", type=str)
def add(deployment_id: str, payload: str) -> None:
    """Add a new revision to a deployment.

    DEPLOYMENT_ID is the deployment UUID.
    PAYLOAD is a JSON string or @file path containing the AddRevisionGQLInputDTO body.

    The payload should include cluster_config, resource_config, image,
    model_runtime_config, model_mount_config, and optionally revision_preset_id.
    """

    from ai.backend.common.dto.manager.v2.deployment.request import (
        AddRevisionGQLInputDTO,
    )

    if payload.startswith("@"):
        with Path(payload[1:]).open() as f:
            data = json.load(f)
    else:
        data = json.loads(payload)

    data["deployment_id"] = deployment_id
    body = AddRevisionGQLInputDTO.model_validate(data)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.add_revision(UUID(deployment_id), body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@revision.command()
@click.argument("revision_id", type=str)
def get(revision_id: str) -> None:
    """Get a revision by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.get_revision(UUID(revision_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
