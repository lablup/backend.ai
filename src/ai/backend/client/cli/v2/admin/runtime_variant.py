"""Admin CLI commands for runtime variants."""

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


@click.group(name="runtime-variant")
def runtime_variant() -> None:
    """Runtime variant admin commands."""


@runtime_variant.command()
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option("--name-contains", default=None, type=str, help="Filter by name substring.")
@click.option("--order-by", multiple=True, help="Order by field:direction (e.g., name:asc).")
@click.option("--json", "json_str", default=None, help="Full search input as JSON string.")
def search(
    limit: int,
    offset: int,
    name_contains: str | None,
    order_by: tuple[str, ...],
    json_str: str | None,
) -> None:
    """Search runtime variants."""
    from ai.backend.common.dto.manager.v2.runtime_variant.request import (
        RuntimeVariantFilter,
        RuntimeVariantOrder,
        SearchRuntimeVariantsInput,
    )
    from ai.backend.common.dto.manager.v2.runtime_variant.types import RuntimeVariantOrderField

    if json_str is not None:
        search_input = _build_dto(SearchRuntimeVariantsInput, json.loads(json_str))
    else:
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


@runtime_variant.command()
@click.argument("body", type=str)
def create(body: str) -> None:
    """Create a new runtime variant (superadmin only).

    BODY is a JSON string. Example: '{"name":"my-runtime","description":"My runtime"}'
    """
    from ai.backend.common.dto.manager.v2.runtime_variant.request import CreateRuntimeVariantInput

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.runtime_variant.create(
                CreateRuntimeVariantInput(
                    name=data["name"],
                    description=data.get("description"),
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@runtime_variant.command()
@click.argument("variant_id", type=click.UUID)
@click.argument("body", type=str)
def update(variant_id: uuid.UUID, body: str) -> None:
    """Update a runtime variant (superadmin only).

    BODY is a JSON string with fields to update.
    """
    from ai.backend.common.dto.manager.v2.runtime_variant.request import UpdateRuntimeVariantInput

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.runtime_variant.update(
                variant_id,
                UpdateRuntimeVariantInput(
                    id=variant_id,
                    name=data.get("name"),
                    description=data.get("description"),
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@runtime_variant.command()
@click.argument("variant_id", type=click.UUID)
def delete(variant_id: uuid.UUID) -> None:
    """Delete a runtime variant (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.runtime_variant.delete(variant_id)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@runtime_variant.command(name="bulk-delete")
@click.argument("ids", nargs=-1, required=True, type=click.UUID)
def bulk_delete(ids: tuple[uuid.UUID, ...]) -> None:
    """Delete multiple runtime variants by ID (superadmin only)."""
    from ai.backend.common.dto.manager.v2.runtime_variant.request import (
        DeleteRuntimeVariantsInput,
    )

    input_dto = DeleteRuntimeVariantsInput(ids=list(ids))

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.runtime_variant.bulk_delete(input_dto)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)
