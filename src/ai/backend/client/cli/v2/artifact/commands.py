"""CLI commands for v2 artifact management."""

from __future__ import annotations

import asyncio
import json

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2.helpers import create_v2_registry, parse_order_options, print_result


@click.group()
def artifacts() -> None:
    """Artifact management commands."""


@artifacts.command(name="admin-search")
@click.option("--limit", default=None, type=int, help="Max results per page.")
@click.option("--offset", default=None, type=int, help="Pagination offset.")
@click.option(
    "--name-contains",
    default=None,
    type=str,
    help="Filter artifacts whose name contains this substring.",
)
@click.option(
    "--type",
    "artifact_type",
    default=None,
    type=str,
    help="Filter by artifact type (e.g., MODEL, PACKAGE, IMAGE).",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., NAME:asc, UPDATED_AT:desc).",
)
@pass_ctx_obj
def admin_search(
    ctx: CLIContext,
    limit: int | None,
    offset: int | None,
    name_contains: str | None,
    artifact_type: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search artifacts with admin scope."""
    from ai.backend.common.dto.manager.v2.artifact.request import (
        AdminSearchArtifactsInput,
        ArtifactFilter,
        ArtifactOrder,
    )
    from ai.backend.common.dto.manager.v2.artifact.types import ArtifactOrderField

    # Build filter only if any filter option is provided
    filter_dto: ArtifactFilter | None = None
    if name_contains is not None or artifact_type is not None:
        from ai.backend.common.dto.manager.query import StringFilter
        from ai.backend.common.dto.manager.v2.artifact.types import ArtifactType, ArtifactTypeFilter

        filter_dto = ArtifactFilter(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            type=ArtifactTypeFilter(equals=ArtifactType(artifact_type))
            if artifact_type is not None
            else None,
        )

    # Build order only if --order-by is provided
    orders = parse_order_options(order_by, ArtifactOrderField, ArtifactOrder) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.artifact.admin_search(
                AdminSearchArtifactsInput(
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


@artifacts.command()
@click.argument("artifact_id")
@pass_ctx_obj
def get(ctx: CLIContext, artifact_id: str) -> None:
    """Get a single artifact by ID."""
    from uuid import UUID

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.artifact.get(UUID(artifact_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@artifacts.command()
@click.argument("artifact_id")
@click.option(
    "--readonly", default=None, type=bool, help="Whether the artifact should be readonly."
)
@click.option(
    "--description", default=None, help="Updated description. Pass empty string to clear."
)
@pass_ctx_obj
def update(
    ctx: CLIContext,
    artifact_id: str,
    readonly: bool | None,
    description: str | None,
) -> None:
    """Update artifact metadata."""
    from uuid import UUID

    from ai.backend.common.api_handlers import SENTINEL, Sentinel
    from ai.backend.common.dto.manager.v2.artifact.request import UpdateArtifactInput

    # SENTINEL means "no change" in the DTO; None means "clear the field".
    # When the CLI user does not pass --description, keep SENTINEL (no change).
    desc_value: str | Sentinel | None = SENTINEL
    if description is not None:
        desc_value = description

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.artifact.update(
                UUID(artifact_id),
                UpdateArtifactInput(readonly=readonly, description=desc_value),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@artifacts.command()
@click.option(
    "--artifact-ids",
    required=True,
    help="JSON array of artifact IDs to delete.",
)
@pass_ctx_obj
def delete(ctx: CLIContext, artifact_ids: str) -> None:
    """Delete multiple artifacts by ID."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.artifact.request import DeleteArtifactsInput

    parsed_ids = [UUID(aid) for aid in json.loads(artifact_ids)]

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.artifact.delete(
                DeleteArtifactsInput(artifact_ids=parsed_ids),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@artifacts.command()
@click.option(
    "--artifact-ids",
    required=True,
    help="JSON array of artifact IDs to restore.",
)
@pass_ctx_obj
def restore(ctx: CLIContext, artifact_ids: str) -> None:
    """Restore previously deleted artifacts."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.artifact.request import RestoreArtifactsInput

    parsed_ids = [UUID(aid) for aid in json.loads(artifact_ids)]

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.artifact.restore(
                RestoreArtifactsInput(artifact_ids=parsed_ids),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@artifacts.command(name="get-revision")
@click.argument("revision_id")
@pass_ctx_obj
def get_revision(ctx: CLIContext, revision_id: str) -> None:
    """Get a single artifact revision by ID."""
    from uuid import UUID

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.artifact.get_revision(UUID(revision_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@artifacts.command(name="approve-revision")
@click.argument("revision_id")
@pass_ctx_obj
def approve_revision(ctx: CLIContext, revision_id: str) -> None:
    """Approve an artifact revision."""
    from uuid import UUID

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.artifact.approve_revision(UUID(revision_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@artifacts.command(name="reject-revision")
@click.argument("revision_id")
@pass_ctx_obj
def reject_revision(ctx: CLIContext, revision_id: str) -> None:
    """Reject an artifact revision."""
    from uuid import UUID

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.artifact.reject_revision(UUID(revision_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@artifacts.command(name="cancel-import")
@click.argument("revision_id")
@pass_ctx_obj
def cancel_import(ctx: CLIContext, revision_id: str) -> None:
    """Cancel an in-progress artifact import."""
    from uuid import UUID

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.artifact.cancel_import(UUID(revision_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@artifacts.command(name="cleanup-revision")
@click.argument("revision_id")
@pass_ctx_obj
def cleanup_revision(ctx: CLIContext, revision_id: str) -> None:
    """Clean up stored artifact revision data."""
    from uuid import UUID

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.artifact.cleanup_revision(UUID(revision_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
