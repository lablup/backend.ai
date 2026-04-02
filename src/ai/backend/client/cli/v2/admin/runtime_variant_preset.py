"""Admin CLI commands for runtime variant presets."""

from __future__ import annotations

import asyncio
import json
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


def _build_dto(dto_cls: type, data: dict[str, Any]) -> Any:
    from pydantic import ValidationError

    try:
        return dto_cls(**data)
    except ValidationError as e:
        click.echo("Validation error:", err=True)
        for err in e.errors():
            field = ".".join(str(loc) for loc in err["loc"])
            click.echo(f"  {field}: {err['msg']}", err=True)
        sys.exit(1)


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


@click.group(name="runtime-variant-preset")
def runtime_variant_preset() -> None:
    """Runtime variant preset admin commands."""


@runtime_variant_preset.command()
@click.option("--limit", type=int, default=20)
@click.option("--offset", type=int, default=0)
@click.option("--runtime-variant-id", default=None, type=click.UUID, help="Filter by variant ID.")
@click.option("--name-contains", default=None, type=str)
@click.option("--order-by", multiple=True, help="e.g., rank:asc")
@click.option("--json", "json_str", default=None, help="Full search input as JSON.")
def search(
    limit: int,
    offset: int,
    runtime_variant_id: uuid.UUID | None,
    name_contains: str | None,
    order_by: tuple[str, ...],
    json_str: str | None,
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

    if json_str is not None:
        search_input = _build_dto(SearchRuntimeVariantPresetsInput, json.loads(json_str))
    else:
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


@runtime_variant_preset.command()
@click.argument("body", type=str)
def create(body: str) -> None:
    """Create a runtime variant preset (superadmin only).

    BODY is a JSON string. Example:
    '{"runtime_variant_id":"<uuid>","name":"tp-size","preset_target":"env","value_type":"int","key":"VLLM_TENSOR_PARALLEL_SIZE"}'
    """
    from ai.backend.common.dto.manager.v2.runtime_variant_preset.request import (
        CreateRuntimeVariantPresetInput,
    )

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    input_dto = _build_dto(CreateRuntimeVariantPresetInput, data)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.runtime_variant_preset.create(input_dto)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@runtime_variant_preset.command()
@click.argument("preset_id", type=click.UUID)
@click.argument("body", type=str)
def update(preset_id: uuid.UUID, body: str) -> None:
    """Update a runtime variant preset (superadmin only)."""
    from ai.backend.common.dto.manager.v2.runtime_variant_preset.request import (
        UpdateRuntimeVariantPresetInput,
    )

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    data["id"] = str(preset_id)
    input_dto = _build_dto(UpdateRuntimeVariantPresetInput, data)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.runtime_variant_preset.update(preset_id, input_dto)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@runtime_variant_preset.command()
@click.argument("preset_id", type=click.UUID)
def delete(preset_id: uuid.UUID) -> None:
    """Delete a runtime variant preset (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.runtime_variant_preset.delete(preset_id)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)
