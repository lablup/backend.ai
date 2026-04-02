"""User-facing CLI commands for model cards."""

from __future__ import annotations

import asyncio
import uuid

import click

from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config, print_result


@click.group(name="model-card")
def model_card() -> None:
    """Model card commands."""


@model_card.command(name="project-search")
@click.argument("project_id", type=click.UUID)
@click.option("--limit", type=int, default=20)
@click.option("--offset", type=int, default=0)
@click.option("--name-contains", default=None, type=str)
def project_search(
    project_id: uuid.UUID,
    limit: int,
    offset: int,
    name_contains: str | None,
) -> None:
    """Search model cards within a MODEL_STORE project."""

    from ai.backend.common.dto.manager.v2.model_card.request import (
        ModelCardFilter,
        SearchModelCardsInput,
    )

    filter_dto: ModelCardFilter | None = None
    if name_contains is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = ModelCardFilter(name=StringFilter(contains=name_contains))

    search_input = SearchModelCardsInput(
        filter=filter_dto,
        limit=limit,
        offset=offset,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.model_card.project_search(project_id, search_input)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


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

    asyncio.run(_run())
