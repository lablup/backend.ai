"""CLI commands for the v2 project resource."""

from __future__ import annotations

import asyncio
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config, print_result


@click.group()
def project() -> None:
    """Project commands."""


@project.command()
@click.argument("project_id", type=click.UUID)
def get(project_id: UUID) -> None:
    """Get a project by UUID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.project.get(project_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
