"""CLI commands for the v2 project resource."""

from __future__ import annotations

import asyncio
from uuid import UUID

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2.helpers import create_v2_registry, print_result


@click.group()
def projects() -> None:
    """Project management commands."""


@projects.command()
@pass_ctx_obj
@click.option("--limit", default=20, help="Maximum number of results to return.")
@click.option("--offset", default=0, help="Number of results to skip.")
def search(ctx: CLIContext, limit: int, offset: int) -> None:
    """Search projects (superadmin only)."""
    from ai.backend.common.dto.manager.v2.group.request import AdminSearchGroupsInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.project.admin_search(
                AdminSearchGroupsInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@projects.command()
@pass_ctx_obj
@click.argument("project_id", type=click.UUID)
def get(ctx: CLIContext, project_id: UUID) -> None:
    """Get a project by UUID."""

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.project.get(project_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
