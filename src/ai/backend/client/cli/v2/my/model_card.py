"""CLI commands for self-service model card operations."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group()
def model_card() -> None:
    """My model card commands."""


@model_card.command()
@click.option("--limit", type=int, default=20, help="Maximum number of results to return.")
@click.option("--offset", type=int, default=0, help="Number of results to skip.")
@click.option("--name-contains", default=None, type=str, help="Filter by name (contains).")
@click.option("--order-by", multiple=True, help="e.g., name:asc, created_at:desc")
def search(
    limit: int,
    offset: int,
    name_contains: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search the model cards I hold through membership."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.model_card.request import (
        ModelCardFilter,
        ModelCardOrder,
        SearchModelCardsInput,
    )
    from ai.backend.common.dto.manager.v2.model_card.types import ModelCardOrderField

    request = SearchModelCardsInput(
        filter=(
            ModelCardFilter(name=StringFilter(contains=name_contains))
            if name_contains is not None
            else None
        ),
        order=(
            parse_order_options(order_by, ModelCardOrderField, ModelCardOrder) if order_by else None
        ),
        limit=limit,
        offset=offset,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.model_card.my_search(request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
