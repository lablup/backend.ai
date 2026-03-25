"""CLI commands for v2 storage namespace management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2.helpers import create_v2_registry, print_result


@click.group()
def storage_namespaces() -> None:
    """Storage namespace management commands."""


@storage_namespaces.command()
@click.option("--storage-id", required=True, help="Storage ID to register namespace for.")
@click.option("--namespace", required=True, help="Namespace bucket or path prefix.")
@pass_ctx_obj
def register(ctx: CLIContext, storage_id: str, namespace: str) -> None:
    """Register a new namespace within a storage."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.storage_namespace.request import (
        RegisterStorageNamespaceInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.storage_namespace.register(
                RegisterStorageNamespaceInput(
                    storage_id=UUID(storage_id),
                    namespace=namespace,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@storage_namespaces.command()
@click.option("--storage-id", required=True, help="Storage ID of the namespace to unregister.")
@click.option("--namespace", required=True, help="Namespace bucket or path prefix to unregister.")
@pass_ctx_obj
def unregister(ctx: CLIContext, storage_id: str, namespace: str) -> None:
    """Unregister a namespace from a storage."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.storage_namespace.request import (
        UnregisterStorageNamespaceInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.storage_namespace.unregister(
                UnregisterStorageNamespaceInput(
                    storage_id=UUID(storage_id),
                    namespace=namespace,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@storage_namespaces.command()
@click.option("--limit", default=None, type=int, help="Max results per page.")
@click.option("--offset", default=None, type=int, help="Pagination offset.")
@pass_ctx_obj
def search(ctx: CLIContext, limit: int | None, offset: int | None) -> None:
    """Search storage namespaces with pagination."""
    from ai.backend.common.dto.manager.v2.storage_namespace.request import (
        AdminSearchStorageNamespacesInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.storage_namespace.search(
                AdminSearchStorageNamespacesInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@storage_namespaces.command(name="get-by-storage")
@click.argument("storage_id")
@pass_ctx_obj
def get_by_storage(ctx: CLIContext, storage_id: str) -> None:
    """Get all namespaces for a given storage."""
    from uuid import UUID

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.storage_namespace.get_by_storage(UUID(storage_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
