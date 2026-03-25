"""CLI commands for v2 VFS storage management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2._helpers import create_v2_registry, print_result


@click.group()
def vfs_storages() -> None:
    """VFS storage management commands."""


@vfs_storages.command()
@click.option("--name", required=True, help="Storage name.")
@click.option("--host", required=True, help="Storage host address.")
@click.option("--base-path", required=True, help="Base path on the storage host.")
@pass_ctx_obj
def create(ctx: CLIContext, name: str, host: str, base_path: str) -> None:
    """Create a new VFS storage."""
    from ai.backend.common.dto.manager.v2.vfs_storage.request import CreateVFSStorageInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.vfs_storage.create(
                CreateVFSStorageInput(name=name, host=host, base_path=base_path),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@vfs_storages.command(name="list-all")
@pass_ctx_obj
def list_all(ctx: CLIContext) -> None:
    """List all VFS storages without pagination."""

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.vfs_storage.list_all()
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@vfs_storages.command()
@click.argument("storage_id")
@pass_ctx_obj
def get(ctx: CLIContext, storage_id: str) -> None:
    """Get a single VFS storage by ID."""
    from uuid import UUID

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.vfs_storage.get(UUID(storage_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@vfs_storages.command()
@click.option("--id", "storage_id", required=True, help="Storage ID to update.")
@click.option("--name", default=None, help="Updated storage name.")
@click.option("--host", default=None, help="Updated host address.")
@click.option("--base-path", default=None, help="Updated base path.")
@pass_ctx_obj
def update(
    ctx: CLIContext,
    storage_id: str,
    name: str | None,
    host: str | None,
    base_path: str | None,
) -> None:
    """Update an existing VFS storage."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.vfs_storage.request import UpdateVFSStorageInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.vfs_storage.update(
                UpdateVFSStorageInput(
                    id=UUID(storage_id),
                    name=name,
                    host=host,
                    base_path=base_path,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@vfs_storages.command()
@click.option("--limit", default=None, type=int, help="Max results per page.")
@click.option("--offset", default=None, type=int, help="Pagination offset.")
@pass_ctx_obj
def search(ctx: CLIContext, limit: int | None, offset: int | None) -> None:
    """Search VFS storages with pagination."""
    from ai.backend.common.dto.manager.v2.vfs_storage.request import AdminSearchVFSStoragesInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.vfs_storage.search(
                AdminSearchVFSStoragesInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@vfs_storages.command()
@click.option("--id", "storage_id", required=True, help="Storage ID to delete.")
@pass_ctx_obj
def delete(ctx: CLIContext, storage_id: str) -> None:
    """Delete a VFS storage."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.vfs_storage.request import DeleteVFSStorageInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.vfs_storage.delete(
                DeleteVFSStorageInput(id=UUID(storage_id)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
