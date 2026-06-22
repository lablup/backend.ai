"""Admin CLI commands for app config definitions."""

from __future__ import annotations

import asyncio
import uuid

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group()
def app_config_definition() -> None:
    """App config definition admin commands (superadmin required)."""


@app_config_definition.command()
@click.option("--config-name", required=True, type=str, help="Unique config name to register.")
def create(config_name: str) -> None:
    """Register a new app config definition."""
    from ai.backend.common.dto.manager.v2.app_config_definition.request import (
        CreateAppConfigDefinitionInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_definition.admin_create(
                CreateAppConfigDefinitionInput(config_name=config_name)
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@app_config_definition.command()
@click.argument("app_config_definition_id", type=click.UUID)
def get(app_config_definition_id: uuid.UUID) -> None:
    """Get an app config definition by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_definition.admin_get(app_config_definition_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@app_config_definition.command()
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option(
    "--config-name-contains",
    default=None,
    type=str,
    help="Filter by config name (substring match).",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., config_name:asc, created_at:desc).",
)
def search(
    limit: int,
    offset: int,
    config_name_contains: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search app config definitions."""
    from ai.backend.common.dto.manager.v2.app_config_definition.request import (
        AppConfigDefinitionFilter,
        AppConfigDefinitionOrder,
        SearchAppConfigDefinitionsInput,
    )
    from ai.backend.common.dto.manager.v2.app_config_definition.types import (
        AppConfigDefinitionOrderField,
    )

    filter_dto: AppConfigDefinitionFilter | None = None
    if config_name_contains is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = AppConfigDefinitionFilter(
            config_name=StringFilter(contains=config_name_contains),
        )

    orders = (
        parse_order_options(order_by, AppConfigDefinitionOrderField, AppConfigDefinitionOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_definition.admin_search(
                SearchAppConfigDefinitionsInput(
                    filter=filter_dto,
                    order=orders,
                    limit=limit,
                    offset=offset,
                )
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@app_config_definition.command()
@click.argument("app_config_definition_id", type=click.UUID)
def purge(app_config_definition_id: uuid.UUID) -> None:
    """Purge an app config definition by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_definition.admin_purge(app_config_definition_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
