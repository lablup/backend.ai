"""CLI commands for self-service project operations."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group()
def project() -> None:
    """My project commands."""


@project.command()
@click.option("--limit", type=int, default=20, help="Maximum number of results to return.")
@click.option("--offset", type=int, default=0, help="Number of results to skip.")
@click.option("--name-contains", default=None, type=str, help="Filter by name (contains).")
@click.option("--is-active/--no-is-active", default=None, help="Filter by active status.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., name:asc, created_at:desc).",
)
def search(
    limit: int,
    offset: int,
    name_contains: str | None,
    is_active: bool | None,
    order_by: tuple[str, ...],
) -> None:
    """Search the projects I am a member of."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.group.request import (
        AdminSearchProjectsInput,
        ProjectFilter,
        ProjectOrder,
    )
    from ai.backend.common.dto.manager.v2.group.types import ProjectOrderField

    filter_dto: ProjectFilter | None = None
    if name_contains is not None or is_active is not None:
        filter_dto = ProjectFilter(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            is_active=is_active,
        )
    request = AdminSearchProjectsInput(
        filter=filter_dto,
        order=parse_order_options(order_by, ProjectOrderField, ProjectOrder) if order_by else None,
        limit=limit,
        offset=offset,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.project.my_search(request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
