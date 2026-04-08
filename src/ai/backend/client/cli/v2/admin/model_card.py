"""Admin CLI commands for model cards."""

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


@click.group(name="model-card")
def model_card() -> None:
    """Model card admin commands."""


@model_card.command()
@click.option("--limit", type=int, default=20)
@click.option("--offset", type=int, default=0)
@click.option("--name-contains", default=None, type=str)
@click.option("--domain-name", default=None, type=str)
@click.option("--project-id", default=None, type=click.UUID)
@click.option("--order-by", multiple=True, help="e.g., name:asc, created_at:desc")
@click.option("--json", "json_str", default=None, help="Full search input as JSON.")
def search(
    limit: int,
    offset: int,
    name_contains: str | None,
    domain_name: str | None,
    project_id: uuid.UUID | None,
    order_by: tuple[str, ...],
    json_str: str | None,
) -> None:
    """Search model cards."""
    from ai.backend.common.dto.manager.v2.model_card.request import (
        ModelCardFilter,
        ModelCardOrder,
        SearchModelCardsInput,
    )
    from ai.backend.common.dto.manager.v2.model_card.types import ModelCardOrderField

    if json_str is not None:
        search_input = _build_dto(SearchModelCardsInput, json.loads(json_str))
    else:
        filter_dto: ModelCardFilter | None = None
        if name_contains is not None or domain_name is not None or project_id is not None:
            from ai.backend.common.dto.manager.query import StringFilter

            filter_dto = ModelCardFilter(
                name=StringFilter(contains=name_contains) if name_contains is not None else None,
                domain_name=domain_name,
                project_id=project_id,
            )
        orders = (
            parse_order_options(order_by, ModelCardOrderField, ModelCardOrder) if order_by else None
        )
        search_input = SearchModelCardsInput(
            filter=filter_dto,
            order=orders,
            limit=limit,
            offset=offset,
        )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.model_card.admin_search(search_input)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@model_card.command()
@click.argument("card_id", type=click.UUID)
def get(card_id: uuid.UUID) -> None:
    """Get a model card by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.model_card.get(card_id)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@model_card.command()
@click.argument("body", type=str)
def create(body: str) -> None:
    """Create a model card.

    BODY is a JSON string.
    """
    from ai.backend.common.dto.manager.v2.model_card.request import CreateModelCardInput

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    input_dto = _build_dto(CreateModelCardInput, data)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.model_card.create(input_dto)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@model_card.command()
@click.argument("card_id", type=click.UUID)
@click.argument("body", type=str)
def update(card_id: uuid.UUID, body: str) -> None:
    """Update a model card."""
    from ai.backend.common.dto.manager.v2.model_card.request import UpdateModelCardInput

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    data["id"] = str(card_id)
    input_dto = _build_dto(UpdateModelCardInput, data)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.model_card.update(card_id, input_dto)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@model_card.command()
@click.argument("card_id", type=click.UUID)
def delete(card_id: uuid.UUID) -> None:
    """Delete a model card."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.model_card.delete(card_id)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@model_card.command(name="bulk-delete")
@click.argument("ids", nargs=-1, required=True, type=click.UUID)
def bulk_delete(ids: tuple[uuid.UUID, ...]) -> None:
    """Delete multiple model cards by ID."""
    from ai.backend.common.dto.manager.v2.model_card.request import DeleteModelCardsInput

    input_dto = DeleteModelCardsInput(ids=list(ids))

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.model_card.bulk_delete(input_dto)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@model_card.command()
@click.option(
    "--project-id", required=True, type=click.UUID, help="MODEL_STORE project UUID to scan."
)
def scan(project_id: uuid.UUID) -> None:
    """Scan vfolders in a MODEL_STORE project and upsert model cards."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.model_card.scan_project(project_id)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)
