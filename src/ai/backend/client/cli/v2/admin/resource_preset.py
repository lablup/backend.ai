"""Admin CLI commands for resource presets."""

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
    """Build a Pydantic DTO from a dict, catching validation errors."""
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
    """Run an async function with SDK error handling."""
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
def resource_preset() -> None:
    """Resource preset admin commands."""


@resource_preset.command()
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option(
    "--name-contains",
    default=None,
    type=str,
    help="Filter presets whose name contains this substring.",
)
@click.option(
    "--resource-group-name-contains",
    default=None,
    type=str,
    help="Filter presets whose resource group name contains this substring.",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., name:asc).",
)
@click.option("--json", "json_str", default=None, help="Full search input as JSON string.")
def search(
    limit: int,
    offset: int,
    name_contains: str | None,
    resource_group_name_contains: str | None,
    order_by: tuple[str, ...],
    json_str: str | None,
) -> None:
    """Search resource presets with admin scope."""
    from ai.backend.common.dto.manager.v2.resource_preset.request import (
        AdminSearchResourcePresetsInput,
        ResourcePresetFilter,
        ResourcePresetOrder,
    )
    from ai.backend.common.dto.manager.v2.resource_preset.types import (
        ResourcePresetOrderField,
    )

    if json_str is not None:
        search_input = _build_dto(AdminSearchResourcePresetsInput, json.loads(json_str))
    else:
        filter_dto: ResourcePresetFilter | None = None
        if name_contains is not None or resource_group_name_contains is not None:
            from ai.backend.common.dto.manager.query import StringFilter

            filter_dto = ResourcePresetFilter(
                name=StringFilter(contains=name_contains) if name_contains is not None else None,
                resource_group_name=(
                    StringFilter(contains=resource_group_name_contains)
                    if resource_group_name_contains is not None
                    else None
                ),
            )

        orders = (
            parse_order_options(order_by, ResourcePresetOrderField, ResourcePresetOrder)
            if order_by
            else None
        )
        search_input = AdminSearchResourcePresetsInput(
            filter=filter_dto,
            order=orders,
            limit=limit,
            offset=offset,
        )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_preset.search(search_input)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@resource_preset.command()
@click.argument("preset_id", type=click.UUID)
def get(preset_id: uuid.UUID) -> None:
    """Get a resource preset by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_preset.get(preset_id)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@resource_preset.command()
@click.argument("body", type=str)
def create(body: str) -> None:
    """Create a new resource preset (superadmin only).

    BODY is a JSON string with resource preset creation fields.

    \b
    Example:
      ./bai admin resource-preset create \\
        '{"name":"my-preset","resource_slots":[{"resource_type":"cpu","quantity":"4"}]}'
    """
    from ai.backend.common.dto.manager.v2.resource_preset.request import (
        CreateResourcePresetInput,
    )

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_preset.create(CreateResourcePresetInput(**data))
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@resource_preset.command()
@click.argument("body", type=str)
def update(body: str) -> None:
    """Update a resource preset (superadmin only).

    BODY is a JSON string with fields to update. The preset is identified by path param.

    \b
    Example:
      ./bai admin resource-preset update \\
        '{"id":"<uuid>","name":"updated-name"}'
    """
    from ai.backend.common.dto.manager.v2.resource_preset.request import (
        UpdateResourcePresetInput,
    )

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    preset_id = data.get("id")
    if not preset_id:
        click.echo("Error: 'id' field is required in the JSON body.", err=True)
        sys.exit(1)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_preset.update(
                uuid.UUID(str(preset_id)),
                UpdateResourcePresetInput(**data),
            )
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@resource_preset.command()
@click.argument("preset_id", type=click.UUID)
def delete(preset_id: uuid.UUID) -> None:
    """Delete a resource preset (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_preset.delete(preset_id)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@resource_preset.command(name="check-availability")
@click.option("--project-id", required=True, type=click.UUID, help="Project ID.")
@click.option("--resource-group", required=True, type=str, help="Resource group name.")
def check_availability(project_id: uuid.UUID, resource_group: str) -> None:
    """Check which resource presets are available for session creation."""
    from ai.backend.common.dto.manager.v2.resource_allocation.request import (
        CheckPresetAvailabilityInput,
    )

    request = CheckPresetAvailabilityInput(
        project_id=project_id,
        resource_group_name=resource_group,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_preset.check_availability(request)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)
