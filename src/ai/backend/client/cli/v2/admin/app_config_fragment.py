"""Admin CLI commands for app config fragments."""

from __future__ import annotations

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
    run_async,
)
from ai.backend.common.data.app_config.types import AppConfigScopeType


@click.group()
def app_config_fragment() -> None:
    """App config fragment admin commands (superadmin required)."""


@app_config_fragment.command()
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
    help="Order by field:direction (e.g., config_name:asc, updated_at:desc).",
)
def search(
    limit: int,
    offset: int,
    config_name_contains: str | None,
    scope_type: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search app config fragments across every scope."""
    from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
        AdminSearchAppConfigFragmentInput,
        AppConfigFragmentFilter,
        AppConfigFragmentOrder,
    )
    from ai.backend.common.dto.manager.v2.app_config_fragment.types import (
        AppConfigFragmentOrderField,
        AppConfigScopeTypeFilter,
    )

    filter_dto: AppConfigFragmentFilter | None = None
    if config_name_contains is not None or scope_type is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = AppConfigFragmentFilter(
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
        parse_order_options(order_by, AppConfigFragmentOrderField, AppConfigFragmentOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_fragment.admin_search(
                AdminSearchAppConfigFragmentInput(
                    filter=filter_dto,
                    order=orders,
                    limit=limit,
                    offset=offset,
                )
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)
