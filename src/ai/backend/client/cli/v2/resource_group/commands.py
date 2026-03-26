"""CLI commands for resource group management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group(name="resource-group")
def resource_group() -> None:
    """Resource group management commands."""


@resource_group.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--name-contains",
    default=None,
    type=str,
    help="Filter resource groups whose name contains this substring.",
)
@click.option(
    "--is-active/--no-is-active",
    default=None,
    help="Filter by active status.",
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
    is_active: bool | None,
    order_by: tuple[str, ...],
) -> None:
    """Search resource groups."""
    from ai.backend.common.dto.manager.v2.resource_group.request import (
        AdminSearchResourceGroupsInput,
        ResourceGroupFilter,
        ResourceGroupOrder,
    )
    from ai.backend.common.dto.manager.v2.resource_group.types import ResourceGroupOrderField

    # Build filter only if any filter option is provided
    filter_dto: ResourceGroupFilter | None = None
    if name_contains is not None or is_active is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = ResourceGroupFilter(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            is_active=is_active,
        )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, ResourceGroupOrderField, ResourceGroupOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_group.search(
                AdminSearchResourceGroupsInput(
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


@resource_group.command()
@click.argument("name", type=str)
def get(name: str) -> None:
    """Get a resource group by name."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_group.get(name)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_group.command()
@click.option("--name", required=True, help="Resource group name.")
@click.option("--domain-name", required=True, help="Domain name.")
@click.option("--description", default=None, help="Description.")
def create(name: str, domain_name: str, description: str | None) -> None:
    """Create a new resource group."""
    from ai.backend.common.dto.manager.v2.resource_group.request import CreateResourceGroupInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_group.create(
                CreateResourceGroupInput(
                    name=name,
                    domain_name=domain_name,
                    description=description,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_group.command()
@click.argument("name", type=str)
def delete(name: str) -> None:
    """Delete a resource group by name."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_group.delete(name)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_group.command(name="resource-info")
@click.argument("name", type=str)
def resource_info(name: str) -> None:
    """Get resource information for a resource group."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_group.get_resource_info(name)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
