"""User-facing CLI commands for the system session environ domain."""

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


@click.group(name="system-session-environ")
def system_session_environ() -> None:
    """System session environ commands."""


@system_session_environ.command(name="value-sources")
def value_sources() -> None:
    """List every value source a system session environ row can carry."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.system_session_environ.list_value_sources()
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@system_session_environ.command(name="scoped-search")
@click.option(
    "--domain",
    "domain_ids",
    type=click.UUID,
    multiple=True,
    help="Domain whose rows are read (repeatable; OR across every scope).",
)
@click.option(
    "--project",
    "project_ids",
    type=click.UUID,
    multiple=True,
    help="Project whose rows are read (repeatable; OR across every scope).",
)
@click.option(
    "--public", is_flag=True, default=False, help="Include the rows registered in public."
)
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--key-contains",
    type=str,
    default=None,
    help="Filter rows whose environment variable name contains this substring.",
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
def scoped_search(
    domain_ids: tuple[UUID, ...],
    project_ids: tuple[UUID, ...],
    public: bool,
    limit: int | None,
    offset: int | None,
    key_contains: str | None,
    deleted: bool | None,
    order_by: tuple[str, ...],
) -> None:
    """Search the system session environ rows the given scopes reach."""
    from ai.backend.common.dto.manager.query import NullableDateTimeFilter, StringFilter
    from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
    from ai.backend.common.dto.manager.v2.system_session_environ.request import (
        ScopedSearchSystemSessionEnvironsInput,
        SystemSessionEnvironFilter,
        SystemSessionEnvironOrder,
    )
    from ai.backend.common.dto.manager.v2.system_session_environ.types import (
        SystemSessionEnvironOrderField,
        SystemSessionEnvironScope,
    )

    scope = SystemSessionEnvironScope(
        domain=[UUIDScope(value=domain_id) for domain_id in domain_ids] or None,
        project=[UUIDScope(value=project_id) for project_id in project_ids] or None,
        public=public,
    )
    environ_filter: SystemSessionEnvironFilter | None = None
    if key_contains is not None or deleted is not None:
        environ_filter = SystemSessionEnvironFilter(
            key=StringFilter(contains=key_contains) if key_contains is not None else None,
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
            result = await registry.system_session_environ.scoped_search(
                ScopedSearchSystemSessionEnvironsInput(
                    scope=scope,
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
