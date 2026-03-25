"""CLI commands for prometheus query preset management."""

from __future__ import annotations

import asyncio
from uuid import UUID

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2._helpers import create_v2_registry, print_result


@click.group()
def prometheus_query_presets() -> None:
    """Prometheus query preset commands."""


@prometheus_query_presets.command()
@click.option("--limit", type=int, default=50, help="Maximum items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@pass_ctx_obj
def search(ctx: CLIContext, limit: int, offset: int) -> None:
    """Search prometheus query definitions."""
    from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
        SearchQueryDefinitionsInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.prometheus_query_preset.search(
                SearchQueryDefinitionsInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@prometheus_query_presets.command()
@click.argument("preset_id", type=str)
@pass_ctx_obj
def get(ctx: CLIContext, preset_id: str) -> None:
    """Get a query definition by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.prometheus_query_preset.get(UUID(preset_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@prometheus_query_presets.command()
@click.option("--name", required=True, help="Human-readable name.")
@click.option("--metric-name", required=True, help="Prometheus metric name.")
@click.option("--query-template", required=True, help="PromQL template with placeholders.")
@click.option("--time-window", default=None, help="Default time window (e.g. '5m', '1h').")
@pass_ctx_obj
def create(
    ctx: CLIContext,
    name: str,
    metric_name: str,
    query_template: str,
    time_window: str | None,
) -> None:
    """Create a new prometheus query definition."""
    from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
        CreateQueryDefinitionInput,
        CreateQueryDefinitionOptionsInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.prometheus_query_preset.create(
                CreateQueryDefinitionInput(
                    name=name,
                    metric_name=metric_name,
                    query_template=query_template,
                    time_window=time_window,
                    options=CreateQueryDefinitionOptionsInput(
                        filter_labels=[],
                        group_labels=[],
                    ),
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@prometheus_query_presets.command()
@click.argument("preset_id", type=str)
@pass_ctx_obj
def delete(ctx: CLIContext, preset_id: str) -> None:
    """Delete a query definition by ID."""
    from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
        DeleteQueryDefinitionInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.prometheus_query_preset.delete(
                DeleteQueryDefinitionInput(id=UUID(preset_id)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
