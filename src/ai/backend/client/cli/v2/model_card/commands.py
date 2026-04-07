"""User-facing CLI commands for model cards."""

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
    """Model card commands."""


@model_card.command(name="project-search")
@click.argument("project_id", type=click.UUID)
@click.option("--limit", type=int, default=20)
@click.option("--offset", type=int, default=0)
@click.option("--name-contains", default=None, type=str)
@click.option("--domain-name", default=None, type=str)
@click.option("--order-by", multiple=True, help="e.g., name:asc, created_at:desc")
@click.option("--json", "json_str", default=None, help="Full search input as JSON.")
def project_search(
    project_id: uuid.UUID,
    limit: int,
    offset: int,
    name_contains: str | None,
    domain_name: str | None,
    order_by: tuple[str, ...],
    json_str: str | None,
) -> None:
    """Search model cards within a MODEL_STORE project."""

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
        if name_contains is not None or domain_name is not None:
            from ai.backend.common.dto.manager.query import StringFilter

            filter_dto = ModelCardFilter(
                name=StringFilter(contains=name_contains) if name_contains is not None else None,
                domain_name=domain_name,
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
            result = await registry.model_card.project_search(project_id, search_input)
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
@click.argument("card_id", type=click.UUID)
@click.option("--project-id", required=True, type=click.UUID, help="Target project UUID.")
@click.option("--revision-preset-id", required=True, type=click.UUID, help="Revision preset UUID.")
@click.option("--resource-group", required=True, type=str, help="Resource group name.")
@click.option("--replicas", default=1, type=int, help="Number of replicas.")
@click.option(
    "--open-to-public/--no-open-to-public",
    "open_to_public",
    default=None,
    help="Override open_to_public. Defaults to the preset value, then False.",
)
@click.option(
    "--replica-count",
    default=None,
    type=int,
    help="Override replica_count. Defaults to the preset value, then the --replicas value.",
)
@click.option(
    "--revision-history-limit",
    default=None,
    type=int,
    help="Override revision_history_limit. Defaults to the preset value, then 10.",
)
@click.option(
    "--strategy",
    default=None,
    type=click.Choice(["ROLLING", "BLUE_GREEN"], case_sensitive=False),
    help="Override deployment strategy type (ROLLING or BLUE_GREEN).",
)
def deploy(
    card_id: uuid.UUID,
    project_id: uuid.UUID,
    revision_preset_id: uuid.UUID,
    resource_group: str,
    replicas: int,
    open_to_public: bool | None,
    replica_count: int | None,
    revision_history_limit: int | None,
    strategy: str | None,
) -> None:
    """Deploy a model card as a new deployment."""
    from ai.backend.common.data.model_deployment.types import DeploymentStrategy
    from ai.backend.common.dto.manager.v2.deployment.request import DeploymentStrategyInput
    from ai.backend.common.dto.manager.v2.model_card.request import DeployModelCardInput

    strategy_input: DeploymentStrategyInput | None = None
    if strategy is not None:
        strategy_input = DeploymentStrategyInput(type=DeploymentStrategy(strategy.upper()))

    deploy_input = DeployModelCardInput(
        project_id=project_id,
        revision_preset_id=revision_preset_id,
        resource_group=resource_group,
        desired_replica_count=replicas,
        open_to_public=open_to_public,
        replica_count=replica_count,
        revision_history_limit=revision_history_limit,
        deployment_strategy=strategy_input,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.model_card.deploy(card_id, deploy_input)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@model_card.command(name="available-presets")
@click.argument("card_id", type=click.UUID)
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option("--runtime-variant-id", default=None, type=click.UUID, help="Filter by variant ID.")
@click.option("--name-contains", default=None, type=str, help="Filter by name substring.")
def available_presets(
    card_id: uuid.UUID,
    limit: int,
    offset: int,
    runtime_variant_id: uuid.UUID | None,
    name_contains: str | None,
) -> None:
    """Search available revision presets for a model card."""
    from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
        DeploymentRevisionPresetFilter,
        SearchDeploymentRevisionPresetsInput,
    )

    filter_dto: DeploymentRevisionPresetFilter | None = None
    if runtime_variant_id is not None or name_contains is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = DeploymentRevisionPresetFilter(
            runtime_variant_id=runtime_variant_id,
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
        )
    search_input = SearchDeploymentRevisionPresetsInput(
        filter=filter_dto,
        limit=limit,
        offset=offset,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.model_card.available_presets(card_id, search_input)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)
