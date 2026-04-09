"""User-facing CLI commands for prometheus query presets.

Read operations (search, get, execute) are available to any authenticated
user since prometheus query presets are a shared catalog of metric query
templates. Write operations (create, update, delete) live under
``admin/prometheus_query_preset.py``.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

import click

if TYPE_CHECKING:
    from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
        MetricLabelEntry,
    )

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group(name="prometheus-query-definition")
def prometheus_query_preset() -> None:
    """Prometheus query definition commands."""


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

    filter_dto: QueryDefinitionFilter | None = None
    if name_contains is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = QueryDefinitionFilter(
            name=StringFilter(contains=name_contains),
        )

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
@click.argument("preset_id", type=click.UUID)
def get(preset_id: UUID) -> None:
    """Get a query definition by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.prometheus_query_preset.get(preset_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


def _parse_label_filters(labels: tuple[str, ...]) -> list[MetricLabelEntry]:
    """Parse ``--label key=value`` options into MetricLabelEntry list."""
    import sys

    from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import MetricLabelEntry

    parsed: list[MetricLabelEntry] = []
    for label in labels:
        if "=" not in label:
            click.echo(f"Invalid label format: {label} (expected key=value)", err=True)
            sys.exit(1)
        key, value = label.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            click.echo(
                f"Invalid label key or value: {label} (both key and value must be non-empty)",
                err=True,
            )
            sys.exit(1)
        parsed.append(MetricLabelEntry(key=key, value=value))
    return parsed


@prometheus_query_preset.command()
@click.argument("preset_id", type=click.UUID)
@click.option("--start", type=click.DateTime(), default=None, help="Start time (ISO8601).")
@click.option("--end", type=click.DateTime(), default=None, help="End time (ISO8601).")
@click.option("--step", type=str, default=None, help="Step duration (e.g. 60s).")
@click.option(
    "--label",
    "labels",
    multiple=True,
    type=str,
    help="Label filter in key=value format (repeatable).",
)
@click.option(
    "--group-labels",
    type=str,
    default=None,
    help="Comma-separated group labels.",
)
@click.option("--time-window", type=str, default=None, help="Time window override.")
def execute(
    preset_id: UUID,
    start: datetime | None,
    end: datetime | None,
    step: str | None,
    labels: tuple[str, ...],
    group_labels: str | None,
    time_window: str | None,
) -> None:
    """Execute a prometheus query definition."""
    from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
        ExecuteQueryDefinitionInput,
        ExecuteQueryDefinitionOptionsInput,
        QueryTimeRangeInputDTO,
    )

    filter_label_entries = _parse_label_filters(labels)

    group_labels_list: list[str] = []
    if group_labels is not None:
        group_labels_list = [gl.strip() for gl in group_labels.split(",") if gl.strip()]

    provided_time_args = sum(value is not None for value in (start, end, step))
    if 0 < provided_time_args < 3:
        raise click.UsageError(
            "Options --start, --end, and --step must be provided together, "
            "or none of them should be specified."
        )

    time_range: QueryTimeRangeInputDTO | None = None
    if provided_time_args == 3:
        time_range = QueryTimeRangeInputDTO(start=start, end=end, step=step)

    request = ExecuteQueryDefinitionInput(
        options=ExecuteQueryDefinitionOptionsInput(
            filter_labels=filter_label_entries,
            group_labels=group_labels_list,
        ),
        time_window=time_window,
        time_range=time_range,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.prometheus_query_preset.execute(preset_id, request)
            print(json.dumps(result.model_dump(mode="json"), indent=2, default=str))
        finally:
            await registry.close()

    asyncio.run(_run())
