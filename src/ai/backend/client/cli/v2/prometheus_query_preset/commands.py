"""CLI commands for prometheus query preset management."""

from __future__ import annotations

import asyncio
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group(name="prometheus-query-preset")
def prometheus_query_preset() -> None:
    """Prometheus query preset commands."""


@prometheus_query_preset.command()
@click.option("--limit", type=int, default=50, help="Maximum items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option(
    "--name-contains",
    default=None,
    type=str,
    help="Filter presets whose name contains this substring.",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., name:asc, created_at:desc, updated_at:desc).",
)
def search(
    limit: int,
    offset: int,
    name_contains: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search prometheus query definitions."""
    from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
        QueryDefinitionFilter,
        QueryDefinitionOrder,
        SearchQueryDefinitionsInput,
    )
    from ai.backend.common.dto.manager.v2.prometheus_query_preset.types import (
        QueryDefinitionOrderField,
    )

    # Build filter only if any filter option is provided
    filter_dto: QueryDefinitionFilter | None = None
    if name_contains is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = QueryDefinitionFilter(
            name=StringFilter(contains=name_contains),
        )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, QueryDefinitionOrderField, QueryDefinitionOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.prometheus_query_preset.search(
                SearchQueryDefinitionsInput(
                    filter=filter_dto,
                    order=orders,
                    limit=limit,
                    offset=offset,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@prometheus_query_preset.command()
@click.argument("preset_id", type=str)
def get(preset_id: str) -> None:
    """Get a query definition by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.prometheus_query_preset.get(UUID(preset_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@prometheus_query_preset.command()
@click.option("--name", required=True, help="Human-readable name.")
@click.option("--metric-name", required=True, help="Prometheus metric name.")
@click.option("--query-template", required=True, help="PromQL template with placeholders.")
@click.option("--time-window", default=None, help="Default time window (e.g. '5m', '1h').")
def create(
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
        registry = await create_v2_registry(load_v2_config())
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


@prometheus_query_preset.command()
@click.argument("preset_id", type=str)
def delete(preset_id: str) -> None:
    """Delete a query definition by ID."""
    from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
        DeleteQueryDefinitionInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.prometheus_query_preset.delete(
                DeleteQueryDefinitionInput(id=UUID(preset_id)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
