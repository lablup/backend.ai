"""CLI commands for v2 artifact registry management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2._helpers import create_v2_registry, print_result


@click.group()
def artifact_registries() -> None:
    """Artifact registry management commands."""


@artifact_registries.command()
@click.argument("registry_id")
@pass_ctx_obj
def get(ctx: CLIContext, registry_id: str) -> None:
    """Get metadata for a single artifact registry by ID."""
    from uuid import UUID

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.artifact_registry.get_registry_meta(UUID(registry_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
