"""Admin CLI commands for the image domain."""

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
def image() -> None:
    """Admin image commands."""


@image.command(name="search")
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option("--name-contains", type=str, default=None, help="Filter images by name (contains).")
@click.option(
    "--status",
    type=click.Choice(["ALIVE", "DELETED"], case_sensitive=False),
    default=None,
    help="Filter images by status.",
)
@click.option(
    "--architecture",
    type=str,
    default=None,
    help="Filter images by architecture (contains).",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., created_at:desc). Fields: name, created_at, last_used.",
)
def search(
    limit: int,
    offset: int,
    name_contains: str | None,
    status: str | None,
    architecture: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search images with admin scope."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.image.request import (
        AdminSearchImagesInput,
        ImageFilterInputDTO,
        ImageOrderByInputDTO,
        ImageStatusFilterInputDTO,
    )
    from ai.backend.common.dto.manager.v2.image.types import ImageOrderField, ImageStatusType

    # Build filter only if any filter option is provided
    filter_dto: ImageFilterInputDTO | None = None
    if any(opt is not None for opt in (name_contains, status, architecture)):
        filter_dto = ImageFilterInputDTO(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            status=(
                ImageStatusFilterInputDTO(equals=ImageStatusType(status))
                if status is not None
                else None
            ),
            architecture=(
                StringFilter(contains=architecture) if architecture is not None else None
            ),
        )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, ImageOrderField, ImageOrderByInputDTO) if order_by else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = AdminSearchImagesInput(
                filter=filter_dto,
                order=orders,
                limit=limit,
                offset=offset,
            )
            result = await registry.image.admin_search(request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# -- Sub-group: alias --


@image.group()
def alias() -> None:
    """Admin image alias commands."""


@alias.command(name="search")
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option(
    "--alias-contains",
    type=str,
    default=None,
    help="Filter aliases by alias string (contains).",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., alias:asc).",
)
def alias_search(
    limit: int,
    offset: int,
    alias_contains: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search image aliases with admin scope."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.image.request import (
        AdminSearchImageAliasesInput,
        ImageAliasFilterInputDTO,
        ImageAliasOrderByInputDTO,
    )

    # Build filter only if alias filter option is provided
    filter_dto: ImageAliasFilterInputDTO | None = None
    if alias_contains is not None:
        filter_dto = ImageAliasFilterInputDTO(
            alias=StringFilter(contains=alias_contains),
        )

    # Build order only if --order-by is provided
    orders = parse_order_options(order_by, str, ImageAliasOrderByInputDTO) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = AdminSearchImageAliasesInput(
                filter=filter_dto,
                order=orders,
                limit=limit,
                offset=offset,
            )
            result = await registry.image.admin_search_image_aliases(request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
