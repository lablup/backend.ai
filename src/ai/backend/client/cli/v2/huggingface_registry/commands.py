"""CLI commands for v2 HuggingFace registry management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2.helpers import create_v2_registry, print_result


@click.group(name="huggingface-registry")
def huggingface_registry() -> None:
    """HuggingFace registry management commands."""


@huggingface_registry.command()
@click.option("--name", required=True, help="Registry name.")
@click.option("--url", required=True, help="HuggingFace Hub URL.")
@click.option("--token", default=None, help="Access token for the registry.")
@pass_ctx_obj
def create(ctx: CLIContext, name: str, url: str, token: str | None) -> None:
    """Create a new HuggingFace registry."""
    from ai.backend.common.dto.manager.v2.huggingface_registry.request import (
        CreateHuggingFaceRegistryInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.huggingface_registry.create(
                CreateHuggingFaceRegistryInput(name=name, url=url, token=token),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@huggingface_registry.command()
@click.option("--limit", default=None, type=int, help="Max results per page.")
@click.option("--offset", default=None, type=int, help="Pagination offset.")
@pass_ctx_obj
def search(ctx: CLIContext, limit: int | None, offset: int | None) -> None:
    """Search HuggingFace registries with pagination."""
    from ai.backend.common.dto.manager.v2.huggingface_registry.request import (
        AdminSearchHuggingFaceRegistriesInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.huggingface_registry.search(
                AdminSearchHuggingFaceRegistriesInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@huggingface_registry.command()
@click.argument("registry_id")
@pass_ctx_obj
def get(ctx: CLIContext, registry_id: str) -> None:
    """Get a single HuggingFace registry by ID."""
    from uuid import UUID

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.huggingface_registry.get(UUID(registry_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@huggingface_registry.command()
@click.option("--id", "registry_id", required=True, help="Registry ID to update.")
@click.option("--name", default=None, help="Updated registry name.")
@click.option("--url", default=None, help="Updated HuggingFace Hub URL.")
@click.option("--token", default=None, help="Updated access token.")
@pass_ctx_obj
def update(
    ctx: CLIContext,
    registry_id: str,
    name: str | None,
    url: str | None,
    token: str | None,
) -> None:
    """Update an existing HuggingFace registry."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.huggingface_registry.request import (
        UpdateHuggingFaceRegistryInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.huggingface_registry.update(
                UpdateHuggingFaceRegistryInput(
                    id=UUID(registry_id),
                    name=name,
                    url=url,
                    token=token,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@huggingface_registry.command()
@click.option("--id", "registry_id", required=True, help="Registry ID to delete.")
@pass_ctx_obj
def delete(ctx: CLIContext, registry_id: str) -> None:
    """Delete a HuggingFace registry."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.huggingface_registry.request import (
        DeleteHuggingFaceRegistryInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.huggingface_registry.delete(
                DeleteHuggingFaceRegistryInput(id=UUID(registry_id)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
