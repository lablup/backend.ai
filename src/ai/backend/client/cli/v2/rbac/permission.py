"""CLI commands for RBAC permission management."""

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


@click.group()
def permission() -> None:
    """RBAC permission commands."""


@permission.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., id:asc, entity_type:desc).",
)
@click.option("--role-id", type=str, default=None, help="Filter by role UUID.")
@click.option("--scope-type", type=str, default=None, help="Filter by scope type (e.g., domain).")
@click.option(
    "--entity-type", type=str, default=None, help="Filter by entity type (e.g., session)."
)
def search(
    limit: int | None,
    offset: int | None,
    order_by: tuple[str, ...],
    role_id: str | None,
    scope_type: str | None,
    entity_type: str | None,
) -> None:
    """Search permissions."""
    from ai.backend.common.dto.manager.v2.rbac.request import (
        AdminSearchPermissionsGQLInput,
        PermissionFilter,
        PermissionOrderBy,
    )
    from ai.backend.common.dto.manager.v2.rbac.types import PermissionOrderField

    # Build filter only if any filter option is provided
    filter_dto: PermissionFilter | None = None
    if any([role_id is not None, scope_type is not None, entity_type is not None]):
        filter_dto = PermissionFilter(
            role_id=UUID(role_id) if role_id is not None else None,
            scope_type=scope_type,
            entity_type=entity_type,
        )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, PermissionOrderField, PermissionOrderBy) if order_by else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.rbac.search_permissions(
                AdminSearchPermissionsGQLInput(
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
