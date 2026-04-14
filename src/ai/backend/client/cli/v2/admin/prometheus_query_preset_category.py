"""Admin CLI commands for the v2 prometheus query preset category resource."""

from __future__ import annotations

import asyncio
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group()
def prometheus_query_preset_category() -> None:
    """Admin prometheus query preset category commands."""


@prometheus_query_preset_category.command()
@click.option("--name", required=True, type=str, help="Unique category name.")
@click.option("--description", default=None, type=str, help="Optional description.")
def create(name: str, description: str | None) -> None:
    """Create a new prometheus query preset category (superadmin only)."""
    from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.request import (
        CreateCategoryInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.prometheus_query_preset_category.create(
                CreateCategoryInput(name=name, description=description),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@prometheus_query_preset_category.command()
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option(
    "--name-contains",
    default=None,
    type=str,
    help="Filter by name (substring match).",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., name:asc, created_at:desc).",
)
def search(
    limit: int,
    offset: int,
    name_contains: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search prometheus query preset categories."""
    from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.request import (
        CategoryFilter,
        CategoryOrder,
        SearchCategoriesInput,
    )
    from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.types import (
        CategoryOrderField,
    )

    filter_dto: CategoryFilter | None = None
    if name_contains is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = CategoryFilter(
            name=StringFilter(contains=name_contains),
        )

    orders = parse_order_options(order_by, CategoryOrderField, CategoryOrder) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.prometheus_query_preset_category.search(
                SearchCategoriesInput(
                    filter=filter_dto,
                    order=orders,
                    limit=limit,
                    offset=offset,
                )
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@prometheus_query_preset_category.command()
@click.argument("category_id", type=click.UUID)
def get(category_id: UUID) -> None:
    """Get a prometheus query preset category by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.prometheus_query_preset_category.get(category_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@prometheus_query_preset_category.command()
@click.argument("category_id", type=click.UUID)
def delete(category_id: UUID) -> None:
    """Delete a prometheus query preset category (superadmin only)."""
    from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.request import (
        DeleteCategoryInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.prometheus_query_preset_category.delete(
                DeleteCategoryInput(id=category_id),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
