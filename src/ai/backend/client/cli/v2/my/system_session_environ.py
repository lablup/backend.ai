"""CLI commands for the system session environ rows applying to the current user."""

from __future__ import annotations

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
    """My system session environ commands."""


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
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., key:asc, created_at:desc).",
)
def search(
    limit: int | None,
    offset: int | None,
    key_contains: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search the enabled rows bound to public, my domain and my projects."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.system_session_environ.request import (
        MySearchSystemSessionEnvironsInput,
        SystemSessionEnvironFilter,
        SystemSessionEnvironOrder,
    )
    from ai.backend.common.dto.manager.v2.system_session_environ.types import (
        SystemSessionEnvironOrderField,
    )

    environ_filter = (
        SystemSessionEnvironFilter(key=StringFilter(contains=key_contains))
        if key_contains is not None
        else None
    )
    orders = (
        parse_order_options(order_by, SystemSessionEnvironOrderField, SystemSessionEnvironOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.system_session_environ.my_search(
                MySearchSystemSessionEnvironsInput(
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
