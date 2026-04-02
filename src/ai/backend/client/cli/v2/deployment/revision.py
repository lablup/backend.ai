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
@click.option(
    "--config",
    required=True,
    type=str,
    help="Revision config as JSON string or @file path. Must include cluster_config, resource_config, image, model_runtime_config, model_mount_config.",
)
@click.option("--preset-id", default=None, type=str, help="Revision preset UUID to apply.")
@click.option(
    "--auto-activate", is_flag=True, default=False, help="Activate immediately after creation."
)
def add(deployment_id: str, config: str, preset_id: str | None, auto_activate: bool) -> None:
    """Add a new revision to a deployment."""

    from ai.backend.common.dto.manager.v2.deployment.request import (
        AddRevisionGQLInputDTO,
    )

    if config.startswith("@"):
        with Path(config[1:]).open() as f:
            data = json.load(f)
    else:
        data = json.loads(config)

    data["deployment_id"] = deployment_id
    if preset_id is not None:
        data["revision_preset_id"] = preset_id
    data["auto_activate"] = auto_activate
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


@revision.command()
@click.argument("deployment_id", type=str)
def current(deployment_id: str) -> None:
    """Get the current active revision of a deployment."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.get_current_revision(UUID(deployment_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@revision.command()
@click.argument("deployment_id", type=str)
@click.option("--name-contains", type=str, default=None, help="Filter by revision name")
@click.option("--limit", type=int, default=20, help="Maximum number of results")
@click.option("--offset", type=int, default=0, help="Offset for pagination")
def search(deployment_id: str, name_contains: str | None, limit: int, offset: int) -> None:
    """Search revisions for a deployment."""

    from ai.backend.common.dto.manager.v2.deployment.request import (
        AdminSearchRevisionsInput,
    )

    body = AdminSearchRevisionsInput(
        filter=f'name_contains: "{name_contains}"' if name_contains else None,
        limit=limit,
        offset=offset,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.search_revisions(UUID(deployment_id), body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@revision.command()
@click.argument("deployment_id", type=str)
@click.argument("revision_id", type=str)
def activate(deployment_id: str, revision_id: str) -> None:
    """Activate a specific revision for a deployment."""

    from ai.backend.common.dto.manager.v2.deployment.request import (
        ActivateRevisionInput,
    )

    body = ActivateRevisionInput(
        deployment_id=UUID(deployment_id),
        revision_id=UUID(revision_id),
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.activate_revision(body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
