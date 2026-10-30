"""CLI commands for self-service image operations."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    EntityLabelTerm,
    create_v2_registry,
    entity_label_filter_options,
    entity_label_relations,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group()
def image() -> None:
    """My image commands."""


@image.command()
@click.option("--limit", type=int, default=20, help="Maximum number of results to return.")
@click.option("--offset", type=int, default=0, help="Number of results to skip.")
@click.option("--name-contains", type=str, default=None, help="Filter by name (contains).")
@entity_label_filter_options
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., created_at:desc). Fields: name, created_at, last_used.",
)
def search(
    limit: int,
    offset: int,
    name_contains: str | None,
    order_by: tuple[str, ...],
    label: tuple[EntityLabelTerm, ...],
) -> None:
    """Search the images I can reach."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.image.request import (
        AdminSearchImagesInput,
        ImageFilterInputDTO,
        ImageOrderByInputDTO,
    )
    from ai.backend.common.dto.manager.v2.image.types import ImageOrderField

    relations = entity_label_relations(label)
    filter_dto: ImageFilterInputDTO | None = None
    if relations or name_contains is not None:
        filter_dto = ImageFilterInputDTO(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            AND=[ImageFilterInputDTO(labels=rel) for rel in relations] or None,
        )
    request = AdminSearchImagesInput(
        filter=filter_dto,
        order=(
            parse_order_options(order_by, ImageOrderField, ImageOrderByInputDTO)
            if order_by
            else None
        ),
        limit=limit,
        offset=offset,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.image.my_search(request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
