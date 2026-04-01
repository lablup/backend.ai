"""Admin CLI commands for deployment revision presets."""

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


@click.group(name="deployment-revision-preset")
def deployment_revision_preset() -> None:
    """Deployment revision preset admin commands."""


@deployment_revision_preset.command()
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
    """Search deployment revision presets."""
    from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
        DeploymentRevisionPresetFilter,
        DeploymentRevisionPresetOrder,
        SearchDeploymentRevisionPresetsInput,
    )
    from ai.backend.common.dto.manager.v2.deployment_revision_preset.types import (
        DeploymentRevisionPresetOrderField,
    )

    if json_str is not None:
        search_input = _build_dto(SearchDeploymentRevisionPresetsInput, json.loads(json_str))
    else:
        filter_dto: DeploymentRevisionPresetFilter | None = None
        if runtime_variant_id is not None or name_contains is not None:
            from ai.backend.common.dto.manager.query import StringFilter

            filter_dto = DeploymentRevisionPresetFilter(
                runtime_variant_id=runtime_variant_id,
                name=StringFilter(contains=name_contains) if name_contains is not None else None,
            )
        orders = (
            parse_order_options(
                order_by,
                DeploymentRevisionPresetOrderField,
                DeploymentRevisionPresetOrder,
            )
            if order_by
            else None
        )
        search_input = SearchDeploymentRevisionPresetsInput(
            filter=filter_dto,
            order=orders,
            limit=limit,
            offset=offset,
        )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment_revision_preset.search(search_input)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@deployment_revision_preset.command()
@click.argument("preset_id", type=click.UUID)
def get(preset_id: uuid.UUID) -> None:
    """Get a deployment revision preset by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment_revision_preset.get(preset_id)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@deployment_revision_preset.command()
@click.argument("body", type=str)
def create(body: str) -> None:
    """Create a deployment revision preset.

    BODY is a JSON string. Example:
    '{"runtime_variant_id":"<uuid>","name":"preset-1"}'
    """
    from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
        CreateDeploymentRevisionPresetInput,
    )

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    input_dto = _build_dto(CreateDeploymentRevisionPresetInput, data)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment_revision_preset.create(input_dto)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@deployment_revision_preset.command()
@click.argument("preset_id", type=click.UUID)
@click.argument("body", type=str)
def update(preset_id: uuid.UUID, body: str) -> None:
    """Update a deployment revision preset."""
    from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
        UpdateDeploymentRevisionPresetInput,
    )

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    data["id"] = str(preset_id)
    input_dto = _build_dto(UpdateDeploymentRevisionPresetInput, data)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment_revision_preset.update(preset_id, input_dto)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@deployment_revision_preset.command()
@click.argument("preset_id", type=click.UUID)
def delete(preset_id: uuid.UUID) -> None:
    """Delete a deployment revision preset."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment_revision_preset.delete(preset_id)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)
