"""CLI commands for v2 artifact management."""

from __future__ import annotations

import asyncio
import json

import click

from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config, print_result

from .revision import revision


@click.group()
def artifact() -> None:
    """Artifact management commands."""


# Register revision sub-group
artifact.add_command(revision)


@artifact.command()
@click.argument("artifact_id")
def get(artifact_id: str) -> None:
    """Get a single artifact by ID."""
    from uuid import UUID

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.artifact.get(UUID(artifact_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@artifact.command()
@click.argument("artifact_id")
@click.option(
    "--readonly", default=None, type=bool, help="Whether the artifact should be readonly."
)
@click.option("--description", default=None, help="Updated description.")
@click.option(
    "--set-null-description",
    is_flag=True,
    default=False,
    help="Clear the description. Mutually exclusive with --description.",
)
def update(
    artifact_id: str,
    readonly: bool | None,
    description: str | None,
    set_null_description: bool,
) -> None:
    """Update artifact metadata."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.artifact.request import UpdateArtifactInput
    from ai.backend.common.tristate.unset import UNSET, Unset

    if description is not None and set_null_description:
        raise click.UsageError("--description and --set-null-description are mutually exclusive.")

    # An option the user did not pass stays UNSET so the field is left unchanged.
    readonly_value: bool | Unset = UNSET if readonly is None else readonly
    desc_value: str | None | Unset = UNSET
    if set_null_description:
        desc_value = None
    elif description is not None:
        desc_value = description

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.artifact.update(
                UUID(artifact_id),
                UpdateArtifactInput(readonly=readonly_value, description=desc_value),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@artifact.command()
@click.option(
    "--artifact-ids",
    required=True,
    help="JSON array of artifact IDs to delete.",
)
def delete(artifact_ids: str) -> None:
    """Delete multiple artifacts by ID."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.artifact.request import DeleteArtifactsInput

    parsed_ids = [UUID(aid) for aid in json.loads(artifact_ids)]

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.artifact.delete(
                DeleteArtifactsInput(artifact_ids=parsed_ids),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@artifact.command()
@click.option(
    "--artifact-ids",
    required=True,
    help="JSON array of artifact IDs to restore.",
)
def restore(artifact_ids: str) -> None:
    """Restore previously deleted artifacts."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.artifact.request import RestoreArtifactsInput

    parsed_ids = [UUID(aid) for aid in json.loads(artifact_ids)]

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.artifact.restore(
                RestoreArtifactsInput(artifact_ids=parsed_ids),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
