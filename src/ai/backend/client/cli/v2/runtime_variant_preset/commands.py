"""User-facing CLI commands for runtime variant presets (search/get)."""

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
def runtime_variant_preset() -> None:
    """Runtime variant preset commands."""


@runtime_variant_preset.command()
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option("--runtime-variant-id", default=None, type=click.UUID, help="Filter by variant ID.")
@click.option("--name-contains", default=None, type=str, help="Filter by name substring.")
@click.option("--order-by", multiple=True, help="Order by field:direction (e.g., rank:asc).")
def search(
    limit: int,
    offset: int,
    runtime_variant_id: uuid.UUID | None,
    name_contains: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search runtime variant presets."""
    from ai.backend.common.dto.manager.v2.runtime_variant_preset.request import (
        RuntimeVariantPresetFilter,
        RuntimeVariantPresetOrder,
        SearchRuntimeVariantPresetsInput,
    )
    from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
        RuntimeVariantPresetOrderField,
    )

    filter_dto: RuntimeVariantPresetFilter | None = None
    if runtime_variant_id is not None or name_contains is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = RuntimeVariantPresetFilter(
            runtime_variant_id=runtime_variant_id,
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
        )
    orders = (
        parse_order_options(order_by, RuntimeVariantPresetOrderField, RuntimeVariantPresetOrder)
        if order_by
        else None
    )
    search_input = SearchRuntimeVariantPresetsInput(
        filter=filter_dto,
        order=orders,
        limit=limit,
        offset=offset,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.runtime_variant_preset.search(search_input)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@runtime_variant_preset.command()
@click.argument("preset_id", type=click.UUID)
def get(preset_id: uuid.UUID) -> None:
    """Get a runtime variant preset by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.runtime_variant_preset.get(preset_id)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)
