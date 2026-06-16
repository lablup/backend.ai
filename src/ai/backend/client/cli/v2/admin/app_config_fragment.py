"""Admin CLI commands for AppConfigFragment (cross-scope search + bulk-only writes)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, cast

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group(name="app-config-fragment")
def app_config_fragment() -> None:
    """Admin AppConfigFragment commands (cross-scope search + bulk-only writes)."""


def _load_items(items_arg: str) -> list[dict[str, Any]]:
    """Accept JSON string or `@file.json` path."""
    if items_arg.startswith("@"):
        return cast("list[dict[str, Any]]", json.loads(Path(items_arg[1:]).read_text()))
    return cast("list[dict[str, Any]]", json.loads(items_arg))


@app_config_fragment.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option("--name-contains", type=str, default=None, help="Filter `name` by substring.")
@click.option("--scope-type", type=str, default=None, help="Filter by scope_type.")
@click.option("--scope-id-contains", type=str, default=None, help="Filter `scope_id` by substring.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction. Fields: scope_type, scope_id, name, created_at, updated_at.",
)
def search(
    limit: int | None,
    offset: int | None,
    name_contains: str | None,
    scope_type: str | None,
    scope_id_contains: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Cross-scope fragment search (superadmin only)."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
        AppConfigFragmentFilter,
        AppConfigFragmentOrder,
        SearchAppConfigFragmentsInput,
    )
    from ai.backend.common.dto.manager.v2.app_config_fragment.types import (
        AppConfigFragmentOrderField,
        AppConfigScopeType,
    )

    filter_dto: AppConfigFragmentFilter | None = None
    if any([name_contains, scope_type, scope_id_contains]):
        filter_dto = AppConfigFragmentFilter(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            scope_type=AppConfigScopeType(scope_type) if scope_type is not None else None,
            scope_id=(
                StringFilter(contains=scope_id_contains) if scope_id_contains is not None else None
            ),
        )

    orders = (
        parse_order_options(order_by, AppConfigFragmentOrderField, AppConfigFragmentOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_fragment.admin_search(
                SearchAppConfigFragmentsInput(
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


@app_config_fragment.command(name="bulk-create")
@click.option(
    "--items",
    required=True,
    help=(
        "JSON list of `{key: {scope_type, scope_id, name}, config}` items, "
        "or `@path/to/items.json`."
    ),
)
def bulk_create(items: str) -> None:
    """Bulk-create fragments (partial-success semantics)."""
    from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
        AdminAppConfigFragmentItemInput,
        AdminBulkCreateAppConfigFragmentsInput,
    )

    parsed = [AdminAppConfigFragmentItemInput.model_validate(item) for item in _load_items(items)]

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_fragment.admin_bulk_create(
                AdminBulkCreateAppConfigFragmentsInput(items=parsed),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@app_config_fragment.command(name="bulk-update")
@click.option(
    "--items",
    required=True,
    help="Same shape as `bulk-create`; replaces `config` wholesale.",
)
def bulk_update(items: str) -> None:
    """Bulk-update fragments (partial-success semantics)."""
    from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
        AdminAppConfigFragmentItemInput,
        AdminBulkUpdateAppConfigFragmentsInput,
    )

    parsed = [AdminAppConfigFragmentItemInput.model_validate(item) for item in _load_items(items)]

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_fragment.admin_bulk_update(
                AdminBulkUpdateAppConfigFragmentsInput(items=parsed),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@app_config_fragment.command(name="bulk-purge")
@click.option(
    "--keys",
    required=True,
    help="JSON list of `{scope_type, scope_id, name}` keys, or `@path/to/keys.json`.",
)
def bulk_purge(keys: str) -> None:
    """Bulk-purge fragments by natural key (partial-success semantics)."""
    from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
        AdminBulkPurgeAppConfigFragmentsInput,
        AppConfigFragmentKeyInput,
    )

    parsed = [AppConfigFragmentKeyInput.model_validate(item) for item in _load_items(keys)]

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_fragment.admin_bulk_purge(
                AdminBulkPurgeAppConfigFragmentsInput(keys=parsed),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
