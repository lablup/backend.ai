"""Admin CLI commands for the v2 prometheus query preset category resource.

Only write operations (create, delete) live here. Read operations
(search, get) are user-facing and live under
``cli/v2/prometheus_query_preset_category/commands.py``.
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
def prometheus_query_preset_category() -> None:
    """Admin prometheus query preset category commands."""


@prometheus_query_preset_category.command()
@click.option("--name", required=True, type=str, help="Unique category name.")
@click.option("--description", default=None, type=str, help="Optional description.")
def create(name: str, description: str | None) -> None:
    """Create a new prometheus query preset category (superadmin only)."""
    from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.request import (
        CreateCategoryInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.prometheus_query_preset_category.create(
                CreateCategoryInput(name=name, description=description),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@prometheus_query_preset_category.command()
@click.argument("category_id", type=click.UUID)
def delete(category_id: UUID) -> None:
    """Delete a prometheus query preset category (superadmin only)."""
    from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.request import (
        DeleteCategoryInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.prometheus_query_preset_category.delete(
                DeleteCategoryInput(id=category_id),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
