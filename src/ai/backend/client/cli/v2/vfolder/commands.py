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


@vfolder.command(name="my-search")
@click.option("--limit", type=int, default=20)
@click.option("--offset", type=int, default=0)
def my_search(limit: int, offset: int) -> None:
    """Search vfolders owned by the current user."""

    from ai.backend.common.dto.manager.v2.vfolder.request import SearchVFoldersInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = SearchVFoldersInput(limit=limit, offset=offset)
            result = await registry.vfolder.my_search(request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


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
        project_id=group_id,
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


@vfolder.command(name="admin-search")
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
def admin_search(limit: int, offset: int) -> None:
    """Search all vfolders (admin)."""

    from ai.backend.common.dto.manager.v2.vfolder.request import SearchVFoldersInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = SearchVFoldersInput(limit=limit, offset=offset)
            result = await registry.vfolder.admin_search(request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@vfolder.command()
@click.argument("vfolder_id", type=click.UUID)
def get(vfolder_id: UUID) -> None:
    """Get a vfolder by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.vfolder.get(vfolder_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@vfolder.command()
@click.argument("vfolder_id", type=click.UUID)
def delete(vfolder_id: UUID) -> None:
    """Delete a vfolder (move to trash)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.vfolder.delete(vfolder_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@vfolder.command()
@click.argument("vfolder_id", type=click.UUID)
def purge(vfolder_id: UUID) -> None:
    """Permanently delete a vfolder."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.vfolder.purge(vfolder_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@vfolder.command()
@click.argument("vfolder_id", type=click.UUID)
@click.option(
    "--project-id",
    required=True,
    type=click.UUID,
    help="Target project UUID where the deployment will be created.",
)
@click.option(
    "--revision-preset-id",
    required=True,
    type=click.UUID,
    help="Deployment revision preset UUID.",
)
@click.option("--resource-group", required=True, type=str, help="Resource group name.")
@click.option(
    "--desired-replica-count",
    default=1,
    type=int,
    show_default=True,
    help="Number of replicas.",
)
@click.option(
    "--open-to-public",
    type=bool,
    default=None,
    help="Override open_to_public. Defaults to the preset value.",
)
@click.option(
    "--replica-count",
    type=int,
    default=None,
    help="Override replica_count. Defaults to the preset value.",
)
@click.option(
    "--revision-history-limit",
    type=int,
    default=None,
    help="Override revision_history_limit. Defaults to the preset value.",
)
def deploy(
    vfolder_id: UUID,
    project_id: UUID,
    revision_preset_id: UUID,
    resource_group: str,
    desired_replica_count: int,
    open_to_public: bool | None,
    replica_count: int | None,
    revision_history_limit: int | None,
) -> None:
    """Deploy a deployment directly from a model VFolder."""
    from ai.backend.common.dto.manager.v2.vfolder.request import DeployVFolderInput

    input_dto = DeployVFolderInput(
        project_id=project_id,
        revision_preset_id=revision_preset_id,
        resource_group=resource_group,
        desired_replica_count=desired_replica_count,
        open_to_public=open_to_public,
        replica_count=replica_count,
        revision_history_limit=revision_history_limit,
        deployment_strategy=None,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.vfolder.deploy(vfolder_id, input_dto)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@vfolder.command()
@click.argument("vfolder_id", type=click.UUID)
@click.argument("path", type=str)
def ls(vfolder_id: UUID, path: str) -> None:
    """List files in a vfolder."""

    from ai.backend.common.dto.manager.v2.vfolder.request import ListFilesInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = ListFilesInput(path=path)
            result = await registry.vfolder.list_files(vfolder_id, request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@vfolder.command()
@click.argument("vfolder_id", type=click.UUID)
@click.argument("path", type=str)
@click.option("--parents/--no-parents", default=True, help="Create parent directories if needed.")
@click.option("--exist-ok", is_flag=True, default=False, help="Do not error if directory exists.")
def mkdir(vfolder_id: UUID, path: str, parents: bool, exist_ok: bool) -> None:
    """Create a directory in a vfolder."""

    from ai.backend.common.dto.manager.v2.vfolder.request import MkdirInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = MkdirInput(path=path, parents=parents, exist_ok=exist_ok)
            result = await registry.vfolder.mkdir(vfolder_id, request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@vfolder.command()
@click.argument("vfolder_id", type=click.UUID)
@click.argument("src", type=str)
@click.argument("dst", type=str)
def mv(vfolder_id: UUID, src: str, dst: str) -> None:
    """Move a file within a vfolder."""

    from ai.backend.common.dto.manager.v2.vfolder.request import MoveFileInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = MoveFileInput(src=src, dst=dst)
            result = await registry.vfolder.move_file(vfolder_id, request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@vfolder.command()
@click.argument("vfolder_id", type=click.UUID)
@click.argument("files", nargs=-1, required=True)
@click.option("--recursive", is_flag=True, default=False, help="Delete directories recursively.")
def rm(vfolder_id: UUID, files: tuple[str, ...], recursive: bool) -> None:
    """Delete files in a vfolder."""

    from ai.backend.common.dto.manager.v2.vfolder.request import DeleteFilesInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = DeleteFilesInput(files=list(files), recursive=recursive)
            result = await registry.vfolder.delete_files(vfolder_id, request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@vfolder.command()
@click.argument("vfolder_id", type=click.UUID)
@click.argument("path", type=str)
@click.option("--archive", is_flag=True, default=False, help="Archive the file for download.")
def download(vfolder_id: UUID, path: str, archive: bool) -> None:
    """Create a download session for a file in a vfolder."""

    from ai.backend.common.dto.manager.v2.vfolder.request import CreateDownloadSessionInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = CreateDownloadSessionInput(path=path, archive=archive)
            result = await registry.vfolder.create_download_session(vfolder_id, request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@vfolder.command()
@click.argument("vfolder_id", type=click.UUID)
@click.option("--name", required=True, help="Name for the cloned vfolder.")
@click.option("--host", default=None, help="Target storage host.")
@click.option(
    "--project-id", default=None, type=click.UUID, help="Project ID for project-owned clone."
)
def clone(vfolder_id: UUID, name: str, host: str | None, project_id: UUID | None) -> None:
    """Clone a vfolder."""

    from ai.backend.common.dto.manager.v2.vfolder.request import CloneVFolderInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = CloneVFolderInput(
                name=name,
                host=host,
                project_id=project_id,
            )
            result = await registry.vfolder.clone(vfolder_id, request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@vfolder.command(name="bulk-delete")
@click.argument("ids", nargs=-1, required=True, type=click.UUID)
def bulk_delete(ids: tuple[UUID, ...]) -> None:
    """Soft-delete multiple vfolders."""

    from ai.backend.common.dto.manager.v2.vfolder.request import BulkDeleteVFoldersInput

    input_dto = BulkDeleteVFoldersInput(ids=list(ids))

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.vfolder.bulk_delete(input_dto)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@vfolder.command(name="bulk-purge")
@click.argument("ids", nargs=-1, required=True, type=click.UUID)
def bulk_purge(ids: tuple[UUID, ...]) -> None:
    """Permanently purge multiple vfolders."""

    from ai.backend.common.dto.manager.v2.vfolder.request import BulkPurgeVFoldersInput

    input_dto = BulkPurgeVFoldersInput(ids=list(ids))

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.vfolder.bulk_purge(input_dto)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
