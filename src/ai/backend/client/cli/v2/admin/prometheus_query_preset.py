"""Admin CLI commands for the v2 prometheus query definition resource.

Write operations (create, update, delete) and template preview live here.
Read operations (search, get, execute) are user-facing and live under
``cli/v2/prometheus_query_preset/commands.py``.
"""

from __future__ import annotations

import asyncio
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    print_result,
)


@click.group()
def prometheus_query_preset() -> None:
    """Admin prometheus query definition commands."""


@prometheus_query_preset.command()
@click.option("--name", required=True, type=str, help="Human-readable name (unique).")
@click.option("--metric-name", required=True, type=str, help="Prometheus metric name.")
@click.option(
    "--query-template", required=True, type=str, help="PromQL template with placeholders."
)
@click.option("--time-window", default=None, type=str, help="Default time window (e.g. '5m').")
@click.option(
    "--filter-label",
    multiple=True,
    help="Allowed filter label key (repeatable).",
)
@click.option(
    "--group-label",
    multiple=True,
    help="Allowed group-by label key (repeatable).",
)
@click.option("--description", default=None, type=str, help="Human-readable description.")
@click.option("--rank", default=0, type=int, help="Sort rank (lower = higher priority).")
@click.option("--category-id", default=None, type=click.UUID, help="Category UUID.")
def create(
    name: str,
    metric_name: str,
    query_template: str,
    time_window: str | None,
    filter_label: tuple[str, ...],
    group_label: tuple[str, ...],
    description: str | None,
    rank: int,
    category_id: UUID | None,
) -> None:
    """Create a new prometheus query definition (superadmin only)."""
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
                        filter_labels=list(filter_label),
                        group_labels=list(group_label),
                    ),
                    description=description,
                    rank=rank,
                    category_id=category_id,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@prometheus_query_preset.command()
@click.argument("preset_id", type=click.UUID)
@click.option("--name", default=None, type=str, help="Updated name.")
@click.option("--metric-name", default=None, type=str, help="Updated Prometheus metric name.")
@click.option("--query-template", default=None, type=str, help="Updated PromQL template.")
@click.option("--time-window", default=None, type=str, help="Updated time window.")
@click.option("--description", default=None, type=str, help="Updated description.")
@click.option("--rank", default=None, type=int, help="Updated sort rank.")
@click.option("--category-id", default=None, type=click.UUID, help="Updated category UUID.")
def update(
    preset_id: UUID,
    name: str | None,
    metric_name: str | None,
    query_template: str | None,
    time_window: str | None,
    description: str | None,
    rank: int | None,
    category_id: UUID | None,
) -> None:
    """Update a prometheus query definition (superadmin only)."""
    from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
        ModifyQueryDefinitionInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.prometheus_query_preset.update(
                preset_id,
                ModifyQueryDefinitionInput(
                    name=name,
                    metric_name=metric_name,
                    query_template=query_template,
                    time_window=time_window,
                    description=description,
                    rank=rank,
                    category_id=category_id,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@prometheus_query_preset.command()
@click.argument("preset_id", type=click.UUID)
def delete(preset_id: UUID) -> None:
    """Delete a prometheus query definition (superadmin only)."""
    from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
        DeleteQueryDefinitionInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.prometheus_query_preset.delete(
                DeleteQueryDefinitionInput(id=preset_id),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@prometheus_query_preset.command()
@click.option(
    "--query-template",
    required=True,
    type=str,
    help="PromQL template to validate.",
)
def preview(query_template: str) -> None:
    """Preview a prometheus query template before saving (superadmin only)."""
    from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
        PreviewQueryDefinitionInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.prometheus_query_preset.admin_preview(
                PreviewQueryDefinitionInput(query_template=query_template),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
