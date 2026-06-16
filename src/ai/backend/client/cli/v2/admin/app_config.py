"""Admin CLI commands for the merged AppConfig view."""

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


@click.group(name="app-config")
def app_config() -> None:
    """Admin merged AppConfig commands."""


@app_config.command()
@click.argument("user_id", type=click.UUID)
@click.argument("name", type=str)
def get(user_id: UUID, name: str) -> None:
    """Read a specific user's merged AppConfig (admin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config.admin_get(user_id, name)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@app_config.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option("--name-contains", type=str, default=None, help="Filter `name` by substring.")
@click.option("--user-id", type=click.UUID, default=None, help="Pin to a single user (UUID).")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction. Fields: name, user_id.",
)
def search(
    limit: int | None,
    offset: int | None,
    name_contains: str | None,
    user_id: UUID | None,
    order_by: tuple[str, ...],
) -> None:
    """Cross-user merged-view search (superadmin only)."""
    from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
    from ai.backend.common.dto.manager.v2.app_config.request import (
        AppConfigFilter,
        AppConfigOrder,
        SearchAppConfigsInput,
    )
    from ai.backend.common.dto.manager.v2.app_config.types import AppConfigOrderField

    filter_dto: AppConfigFilter | None = None
    if name_contains is not None or user_id is not None:
        filter_dto = AppConfigFilter(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            user_id=UUIDFilter(equals=user_id) if user_id is not None else None,
        )

    orders = (
        parse_order_options(order_by, AppConfigOrderField, AppConfigOrder) if order_by else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config.admin_search(
                SearchAppConfigsInput(
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
