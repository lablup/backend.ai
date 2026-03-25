"""CLI commands for artifact revision management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2.helpers import create_v2_registry, print_result


@click.group()
def revision() -> None:
    """Artifact revision commands."""


@revision.command()
@click.argument("revision_id")
@pass_ctx_obj
def get(ctx: CLIContext, revision_id: str) -> None:
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


@revision.command()
@click.argument("revision_id")
@pass_ctx_obj
def approve(ctx: CLIContext, revision_id: str) -> None:
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


@revision.command()
@click.argument("revision_id")
@pass_ctx_obj
def reject(ctx: CLIContext, revision_id: str) -> None:
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


@revision.command(name="cancel-import")
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


@revision.command()
@click.argument("revision_id")
@pass_ctx_obj
def cleanup(ctx: CLIContext, revision_id: str) -> None:
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
