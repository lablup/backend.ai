"""CLI commands for the merged AppConfig view.

Public entrypoint exposes only the read paths that any authenticated
user can hit. Self-service writes live under `bai my app-config`;
admin operations live under `bai admin app-config`.
"""

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
    """Merged AppConfig commands (per-policy resolved view)."""


@app_config.command()
@click.option(
    "--user-id",
    "user_ids",
    type=click.UUID,
    multiple=True,
    required=True,
    help="Target user UUID to scope the search to (repeatable, OR'd). "
    "Pass your own id for self-service.",
)
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option("--name-contains", type=str, default=None, help="Filter `name` by substring.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction. Fields: name, user_id.",
)
def search(
    user_ids: tuple[UUID, ...],
    limit: int | None,
    offset: int | None,
    name_contains: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Scoped merged-view search (auth required, RBAC-gated).

    `--user-id` is the scope; pass your own id for self-service.
    """
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.app_config.request import (
        AppConfigFilter,
        AppConfigOrder,
        AppConfigScope,
        ScopedSearchAppConfigsInput,
    )
    from ai.backend.common.dto.manager.v2.app_config.types import AppConfigOrderField

    filter_dto: AppConfigFilter | None = None
    if name_contains is not None:
        filter_dto = AppConfigFilter(name=StringFilter(contains=name_contains))

    orders = (
        parse_order_options(order_by, AppConfigOrderField, AppConfigOrder) if order_by else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config.scoped_search(
                ScopedSearchAppConfigsInput(
                    scope=AppConfigScope(user_ids=list(user_ids)),
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
