"""Admin CLI commands for the system session environ domain."""

from __future__ import annotations

from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
    run_async,
)
from ai.backend.common.data.system_session_environ.types import SystemSessionEnvironScopeType

_SCOPE_TYPE_CHOICE = click.Choice([
    scope_type.value for scope_type in SystemSessionEnvironScopeType
])


@click.group(name="system-session-environ")
def system_session_environ() -> None:
    """Admin system session environ commands."""


@system_session_environ.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--key-contains",
    type=str,
    default=None,
    help="Filter rows whose environment variable name contains this substring.",
)
@click.option(
    "--value-source",
    type=str,
    default=None,
    help="Filter by which value of the starting session is injected (a value source name).",
)
@click.option(
    "--scope-type",
    type=_SCOPE_TYPE_CHOICE,
    default=None,
    help="Filter by the kind of scope the row is bound to.",
)
@click.option(
    "--scope-id",
    type=click.UUID,
    default=None,
    help="Filter by the id of the public entity, the domain or the project.",
)
@click.option(
    "--deleted/--no-deleted",
    default=None,
    help="Filter by whether the row is soft-deleted.",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., key:asc, created_at:desc).",
)
def search(
    limit: int | None,
    offset: int | None,
    key_contains: str | None,
    value_source: str | None,
    scope_type: str | None,
    scope_id: UUID | None,
    deleted: bool | None,
    order_by: tuple[str, ...],
) -> None:
    """Search every system session environ row, at every scope (superadmin only)."""
    from ai.backend.common.dto.manager.query import (
        NullableDateTimeFilter,
        StringFilter,
        UUIDFilter,
    )
    from ai.backend.common.dto.manager.v2.system_session_environ.request import (
        AdminSearchSystemSessionEnvironsInput,
        SystemSessionEnvironFilter,
        SystemSessionEnvironOrder,
        SystemSessionEnvironScopeTypeFilter,
        SystemSessionEnvironValueSourceFilter,
    )
    from ai.backend.common.dto.manager.v2.system_session_environ.types import (
        SystemSessionEnvironOrderField,
    )

    environ_filter: SystemSessionEnvironFilter | None = None
    if any(
        option is not None for option in (key_contains, value_source, scope_type, scope_id, deleted)
    ):
        environ_filter = SystemSessionEnvironFilter(
            key=StringFilter(contains=key_contains) if key_contains is not None else None,
            value_source=(
                SystemSessionEnvironValueSourceFilter(equals=value_source)
                if value_source is not None
                else None
            ),
            scope_type=(
                SystemSessionEnvironScopeTypeFilter(
                    equals=SystemSessionEnvironScopeType(scope_type)
                )
                if scope_type is not None
                else None
            ),
            scope_id=UUIDFilter(equals=scope_id) if scope_id is not None else None,
            deleted_at=NullableDateTimeFilter(is_null=not deleted) if deleted is not None else None,
        )

    orders = (
        parse_order_options(order_by, SystemSessionEnvironOrderField, SystemSessionEnvironOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.system_session_environ.admin_search(
                AdminSearchSystemSessionEnvironsInput(
                    filter=environ_filter,
                    order=orders,
                    limit=limit,
                    offset=offset,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)
