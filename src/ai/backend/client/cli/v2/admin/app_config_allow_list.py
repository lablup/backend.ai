"""Admin CLI commands for app config allow-list entries."""

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
from ai.backend.common.data.app_config.types import AppConfigScopeType


@click.group()
def app_config_allow_list() -> None:
    """App config allow-list admin commands (superadmin required)."""


@app_config_allow_list.command()
@click.option("--config-name", required=True, type=str, help="Registered config name to gate.")
@click.option(
    "--scope-type",
    required=True,
    type=click.Choice([scope_type.value for scope_type in AppConfigScopeType]),
    help="Scope type the entry permits writes at.",
)
def create(config_name: str, scope_type: str) -> None:
    """Register a new app config allow-list entry."""
    from ai.backend.common.dto.manager.v2.app_config_allow_list.request import (
        CreateAppConfigAllowListInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_allow_list.admin_create(
                CreateAppConfigAllowListInput(
                    config_name=config_name,
                    scope_type=AppConfigScopeType(scope_type),
                )
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@app_config_allow_list.command()
@click.argument("app_config_allow_list_id", type=click.UUID)
def get(app_config_allow_list_id: uuid.UUID) -> None:
    """Get an app config allow-list entry by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_allow_list.admin_get(app_config_allow_list_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@app_config_allow_list.command()
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option(
    "--config-name-contains",
    default=None,
    type=str,
    help="Filter by config name (substring match).",
)
@click.option(
    "--scope-type",
    default=None,
    type=click.Choice([scope_type.value for scope_type in AppConfigScopeType]),
    help="Filter by scope type (exact match).",
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
    scope_type: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search app config allow-list entries."""
    from ai.backend.common.dto.manager.v2.app_config_allow_list.request import (
        AppConfigAllowListFilter,
        AppConfigAllowListOrder,
        SearchAppConfigAllowListInput,
    )
    from ai.backend.common.dto.manager.v2.app_config_allow_list.types import (
        AppConfigAllowListOrderField,
        AppConfigScopeTypeFilter,
    )

    filter_dto: AppConfigAllowListFilter | None = None
    if config_name_contains is not None or scope_type is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = AppConfigAllowListFilter(
            config_name=(
                StringFilter(contains=config_name_contains)
                if config_name_contains is not None
                else None
            ),
            scope_type=(
                AppConfigScopeTypeFilter(equals=AppConfigScopeType(scope_type))
                if scope_type is not None
                else None
            ),
        )

    orders = (
        parse_order_options(order_by, AppConfigAllowListOrderField, AppConfigAllowListOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_allow_list.admin_search(
                SearchAppConfigAllowListInput(
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


@app_config_allow_list.command()
@click.argument("app_config_allow_list_id", type=click.UUID)
def purge(app_config_allow_list_id: uuid.UUID) -> None:
    """Purge an app config allow-list entry by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_allow_list.admin_purge(app_config_allow_list_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
