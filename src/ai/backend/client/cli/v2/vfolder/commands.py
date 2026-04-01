"""User-facing CLI commands for the v2 VFolder domain."""

from __future__ import annotations

import asyncio
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config, print_result


@click.group()
def vfolder() -> None:
    """VFolder management commands."""


@vfolder.command(name="project-search")
@click.argument("project_id", type=str)
@click.option("--limit", type=int, default=20)
@click.option("--offset", type=int, default=0)
def project_search(project_id: str, limit: int, offset: int) -> None:
    """Search vfolders within a project."""

    from ai.backend.common.dto.manager.v2.vfolder.request import SearchVFoldersInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = SearchVFoldersInput(limit=limit, offset=offset)
            result = await registry.vfolder.project_search(UUID(project_id), request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
