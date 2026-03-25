"""CLI commands for v2 object storage management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group(name="object-storage")
def object_storage() -> None:
    """Object storage management commands."""


@object_storage.command()
@click.option("--name", required=True, help="Object storage name.")
@click.option("--host", required=True, help="Host address of the object storage.")
@click.option("--access-key", required=True, help="Access key for authentication.")
@click.option("--secret-key", required=True, help="Secret key for authentication.")
@click.option("--endpoint", required=True, help="Endpoint URL of the object storage.")
@click.option("--region", required=True, help="Region of the object storage.")
def create(
    name: str,
    host: str,
    access_key: str,
    secret_key: str,
    endpoint: str,
    region: str,
) -> None:
    """Create a new object storage."""
    from ai.backend.common.dto.manager.v2.object_storage.request import CreateObjectStorageInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.object_storage.create(
                CreateObjectStorageInput(
                    name=name,
                    host=host,
                    access_key=access_key,
                    secret_key=secret_key,
                    endpoint=endpoint,
                    region=region,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@object_storage.command()
@click.argument("storage_id")
def get(storage_id: str) -> None:
    """Get a single object storage by ID."""
    from uuid import UUID

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.object_storage.get(UUID(storage_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@object_storage.command()
@click.option("--id", "storage_id", required=True, help="Object storage ID to update.")
@click.option("--name", default=None, help="Updated name.")
@click.option("--host", default=None, help="Updated host address.")
@click.option("--access-key", default=None, help="Updated access key.")
@click.option("--secret-key", default=None, help="Updated secret key.")
@click.option("--endpoint", default=None, help="Updated endpoint URL.")
@click.option("--region", default=None, help="Updated region. Pass empty string to clear.")
def update(
    storage_id: str,
    name: str | None,
    host: str | None,
    access_key: str | None,
    secret_key: str | None,
    endpoint: str | None,
    region: str | None,
) -> None:
    """Update an existing object storage."""
    from uuid import UUID

    from ai.backend.common.api_handlers import SENTINEL, Sentinel
    from ai.backend.common.dto.manager.v2.object_storage.request import UpdateObjectStorageInput

    # SENTINEL means "no change", None means "clear the field".
    # When the CLI user does not pass --region, keep SENTINEL (no change).
    # When they pass an empty string, interpret as None (clear).
    region_value: str | Sentinel | None = SENTINEL
    if region is not None:
        region_value = region if region else None

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.object_storage.update(
                UpdateObjectStorageInput(
                    id=UUID(storage_id),
                    name=name,
                    host=host,
                    access_key=access_key,
                    secret_key=secret_key,
                    endpoint=endpoint,
                    region=region_value,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@object_storage.command()
@click.option("--limit", default=None, type=int, help="Max results per page.")
@click.option("--offset", default=None, type=int, help="Pagination offset.")
@click.option(
    "--name-contains",
    default=None,
    type=str,
    help="Filter storages whose name contains this substring.",
)
@click.option(
    "--host-contains",
    default=None,
    type=str,
    help="Filter storages whose host contains this substring.",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., name:asc, created_at:desc).",
)
def search(
    limit: int | None,
    offset: int | None,
    name_contains: str | None,
    host_contains: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search object storages with admin scope."""
    from ai.backend.common.dto.manager.v2.object_storage.request import (
        AdminSearchObjectStoragesInput,
        ObjectStorageFilter,
        ObjectStorageOrder,
    )
    from ai.backend.common.dto.manager.v2.object_storage.types import ObjectStorageOrderField

    # Build filter only if any filter option is provided
    filter_dto: ObjectStorageFilter | None = None
    if name_contains is not None or host_contains is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = ObjectStorageFilter(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            host=StringFilter(contains=host_contains) if host_contains is not None else None,
        )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, ObjectStorageOrderField, ObjectStorageOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.object_storage.search(
                AdminSearchObjectStoragesInput(
                    filter=filter_dto,
                    order=orders,
                    limit=limit,
                    offset=offset,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@object_storage.command()
@click.option("--id", "storage_id", required=True, help="Object storage ID to delete.")
def delete(storage_id: str) -> None:
    """Delete an object storage."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.object_storage.request import DeleteObjectStorageInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.object_storage.delete(
                DeleteObjectStorageInput(id=UUID(storage_id)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
