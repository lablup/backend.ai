"""Admin CLI commands for container registries."""

from __future__ import annotations

import asyncio
import uuid

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group()
def container_registry() -> None:
    """Container registry admin commands."""


@container_registry.command()
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option(
    "--registry-name",
    default=None,
    type=str,
    help="Filter registries whose name contains this substring.",
)
@click.option(
    "--type",
    "registry_type",
    default=None,
    type=str,
    help="Filter by registry type (e.g., docker, harbor, harbor2).",
)
@click.option(
    "--is-global/--no-is-global",
    default=None,
    help="Filter by global accessibility.",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., registry_name:asc, type:desc).",
)
def search(
    limit: int,
    offset: int,
    registry_name: str | None,
    registry_type: str | None,
    is_global: bool | None,
    order_by: tuple[str, ...],
) -> None:
    """Search container registries with admin scope."""
    from ai.backend.common.dto.manager.v2.container_registry.request import (
        AdminSearchContainerRegistriesInput,
        ContainerRegistryFilter,
        ContainerRegistryOrder,
    )
    from ai.backend.common.dto.manager.v2.container_registry.types import (
        ContainerRegistryOrderField,
    )

    # Build filter only if any filter option is provided
    filter_dto: ContainerRegistryFilter | None = None
    if registry_name is not None or registry_type is not None or is_global is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        type_filter = None
        if registry_type is not None:
            from ai.backend.common.container_registry import ContainerRegistryType
            from ai.backend.common.dto.manager.v2.container_registry.types import (
                ContainerRegistryTypeFilter,
            )

            type_filter = ContainerRegistryTypeFilter(
                equals=ContainerRegistryType(registry_type),
            )

        filter_dto = ContainerRegistryFilter(
            registry_name=StringFilter(contains=registry_name)
            if registry_name is not None
            else None,
            type=type_filter,
            is_global=is_global,
        )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, ContainerRegistryOrderField, ContainerRegistryOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = AdminSearchContainerRegistriesInput(
                filter=filter_dto,
                order=orders,
                limit=limit,
                offset=offset,
            )
            result = await registry.container_registry.admin_search(request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@container_registry.command()
@click.argument("body", type=str)
def create(body: str) -> None:
    """Create a new container registry (superadmin only).

    BODY is a JSON string with container registry creation fields.
    """
    import json
    import sys

    from ai.backend.common.dto.manager.v2.container_registry.request import (
        CreateContainerRegistryInput,
    )

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.container_registry.admin_create(
                CreateContainerRegistryInput(**data)
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@container_registry.command()
@click.argument("body", type=str)
def update(body: str) -> None:
    """Update a container registry (superadmin only).

    BODY is a JSON string with fields to update. Must include "id" (UUID).
    """
    import json
    import sys

    from ai.backend.common.dto.manager.v2.container_registry.request import (
        UpdateContainerRegistryInput,
    )

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.container_registry.admin_update(
                UpdateContainerRegistryInput(**data)
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@container_registry.command()
@click.argument("registry_id", type=click.UUID)
def delete(registry_id: uuid.UUID) -> None:
    """Delete a container registry (superadmin only). This is a hard delete."""
    from ai.backend.common.dto.manager.v2.container_registry.request import (
        DeleteContainerRegistryInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.container_registry.admin_delete(
                DeleteContainerRegistryInput(id=registry_id)
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
