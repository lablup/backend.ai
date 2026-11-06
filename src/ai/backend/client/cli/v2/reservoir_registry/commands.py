"""CLI commands for v2 Reservoir registry management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config, print_result


@click.group(name="reservoir-registry")
def reservoir_registry() -> None:
    """Reservoir registry management commands."""


@reservoir_registry.command()
@click.option("--name", required=True, help="Registry name.")
@click.option("--endpoint", required=True, help="Reservoir endpoint URL.")
@click.option("--access-key", required=True, help="Access key for authentication.")
@click.option("--secret-key", required=True, help="Secret key for authentication.")
@click.option("--api-version", required=True, help="API version string.")
def create(
    name: str,
    endpoint: str,
    access_key: str,
    secret_key: str,
    api_version: str,
) -> None:
    """Create a new Reservoir registry."""
    from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
        CreateReservoirRegistryInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.reservoir_registry.create(
                CreateReservoirRegistryInput(
                    name=name,
                    endpoint=endpoint,
                    access_key=access_key,
                    secret_key=secret_key,
                    api_version=api_version,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@reservoir_registry.command()
@click.option("--limit", default=None, type=int, help="Max results per page.")
@click.option("--offset", default=None, type=int, help="Pagination offset.")
def search(limit: int | None, offset: int | None) -> None:
    """Search Reservoir registries with pagination."""
    from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
        AdminSearchReservoirRegistriesInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.reservoir_registry.search(
                AdminSearchReservoirRegistriesInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@reservoir_registry.command()
@click.argument("registry_id")
def get(registry_id: str) -> None:
    """Get a single Reservoir registry by ID."""
    from uuid import UUID

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.reservoir_registry.get(UUID(registry_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@reservoir_registry.command()
@click.option("--id", "registry_id", required=True, help="Registry ID to update.")
@click.option("--name", default=None, help="Updated registry name.")
@click.option("--endpoint", default=None, help="Updated endpoint URL.")
@click.option("--access-key", default=None, help="Updated access key.")
@click.option("--secret-key", default=None, help="Updated secret key.")
@click.option("--api-version", default=None, help="Updated API version.")
def update(
    registry_id: str,
    name: str | None,
    endpoint: str | None,
    access_key: str | None,
    secret_key: str | None,
    api_version: str | None,
) -> None:
    """Update an existing Reservoir registry."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
        UpdateReservoirRegistryInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.reservoir_registry.update(
                UpdateReservoirRegistryInput(
                    id=UUID(registry_id),
                    name=name,
                    endpoint=endpoint,
                    access_key=access_key,
                    secret_key=secret_key,
                    api_version=api_version,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@reservoir_registry.command()
@click.option("--id", "registry_id", required=True, help="Registry ID to delete.")
def delete(registry_id: str) -> None:
    """Delete a Reservoir registry."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
        DeleteReservoirRegistryInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.reservoir_registry.delete(
                DeleteReservoirRegistryInput(id=UUID(registry_id)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
