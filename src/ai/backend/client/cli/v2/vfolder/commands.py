"""User-facing CLI commands for the v2 VFolder domain."""

from __future__ import annotations

import asyncio
from pathlib import Path
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


@vfolder.command()
@click.option("--name", required=True, help="VFolder name.")
@click.option(
    "--usage-mode",
    default="general",
    type=click.Choice(["general", "model", "data"], case_sensitive=False),
    help="Usage mode of the vfolder.",
)
@click.option("--group", "group_id", default=None, type=click.UUID, help="Project UUID.")
@click.option("--host", default=None, type=str, help="Storage host.")
@click.option("--cloneable", is_flag=True, default=False, help="Allow cloning.")
def create(
    name: str,
    usage_mode: str,
    group_id: UUID | None,
    host: str | None,
    cloneable: bool,
) -> None:
    """Create a new vfolder."""

    from ai.backend.common.dto.manager.v2.vfolder.request import CreateVFolderInput
    from ai.backend.common.dto.manager.v2.vfolder.types import VFolderUsageMode

    input_dto = CreateVFolderInput(
        name=name,
        usage_mode=VFolderUsageMode(usage_mode),
        group_id=group_id,
        host=host,
        cloneable=cloneable,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.vfolder.create(input_dto)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@vfolder.command()
@click.argument("vfolder_id", type=click.UUID)
@click.argument("filenames", nargs=-1, required=True)
def upload(vfolder_id: UUID, filenames: tuple[str, ...]) -> None:
    """Upload files to a vfolder.

    Creates an upload session per file and prints the session token/url.
    The actual file transfer uses TUS protocol to the returned URL.
    """

    from ai.backend.common.dto.manager.v2.vfolder.request import CreateUploadSessionInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            for filepath in filenames:
                p = Path(filepath)
                size = p.stat().st_size
                filename = p.name
                request = CreateUploadSessionInput(path=filename, size=size)
                result = await registry.vfolder.create_upload_session(vfolder_id, request)
                print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
