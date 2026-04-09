"""User-facing CLI commands for runtime variants (search/get)."""

from __future__ import annotations

import asyncio
import sys
import uuid
from typing import Any

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


def _run_async(coro_fn: Any) -> None:
    from ai.backend.client.exceptions import BackendAPIError

    try:
        asyncio.run(coro_fn())
    except BackendAPIError as e:
        data = e.args[2] if len(e.args) > 2 else {}
        title = data.get("title", "") if isinstance(data, dict) else ""
        msg = data.get("msg", "") if isinstance(data, dict) else ""
        status = e.args[0] if e.args else "?"
        detail = title or msg or str(e)
        click.echo(f"Error ({status}): {detail}", err=True)
        sys.exit(1)


@click.group()
def runtime_variant() -> None:
    """Runtime variant commands."""


@runtime_variant.command()
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option("--name-contains", default=None, type=str, help="Filter by name substring.")
@click.option("--order-by", multiple=True, help="Order by field:direction (e.g., name:asc).")
def search(
    limit: int,
    offset: int,
    name_contains: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search runtime variants."""
    from ai.backend.common.dto.manager.v2.runtime_variant.request import (
        RuntimeVariantFilter,
        RuntimeVariantOrder,
        SearchRuntimeVariantsInput,
    )
    from ai.backend.common.dto.manager.v2.runtime_variant.types import RuntimeVariantOrderField

    filter_dto: RuntimeVariantFilter | None = None
    if name_contains is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = RuntimeVariantFilter(
            name=StringFilter(contains=name_contains),
        )
    orders = (
        parse_order_options(order_by, RuntimeVariantOrderField, RuntimeVariantOrder)
        if order_by
        else None
    )
    search_input = SearchRuntimeVariantsInput(
        filter=filter_dto,
        order=orders,
        limit=limit,
        offset=offset,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.runtime_variant.search(search_input)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@runtime_variant.command()
@click.argument("variant_id", type=click.UUID)
def get(variant_id: uuid.UUID) -> None:
    """Get a runtime variant by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.runtime_variant.get(variant_id)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)
