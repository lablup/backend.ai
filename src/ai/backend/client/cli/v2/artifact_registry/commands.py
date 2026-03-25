"""CLI commands for v2 artifact registry management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config, print_result


@click.group(name="artifact-registry")
def artifact_registry() -> None:
    """Artifact registry management commands."""


@artifact_registry.command()
@click.argument("registry_id")
def get(registry_id: str) -> None:
    """Get metadata for a single artifact registry by ID."""
    from uuid import UUID

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.artifact_registry.get_registry_meta(UUID(registry_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
