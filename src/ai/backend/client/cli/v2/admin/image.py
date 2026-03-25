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


@image.command()
@click.argument("image_id", type=click.UUID)
def forget(image_id: str) -> None:
    """Forget (soft-delete) an image by ID."""
    from ai.backend.common.dto.manager.v2.image.request import ForgetImageInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.image.admin_forget(ForgetImageInput(image_id=image_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@image.command()
@click.argument("image_id", type=click.UUID)
def purge(image_id: str) -> None:
    """Purge (hard-delete) an image by ID."""
    from ai.backend.common.dto.manager.v2.image.request import PurgeImageInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.image.admin_purge(PurgeImageInput(image_id=image_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@image.command()
@click.argument("body", type=str)
def update(body: str) -> None:
    """Update an image by ID (superadmin only).

    BODY is a JSON string with image_id and fields to update.
    """
    import json
    import sys

    from ai.backend.common.dto.manager.v2.image.request import UpdateImageInput

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.image.admin_update(UpdateImageInput(**data))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@alias.command(name="create")
@click.argument("image_id", type=click.UUID)
@click.argument("alias_name")
def alias_create(image_id: str, alias_name: str) -> None:
    """Create an alias for an image."""
    from ai.backend.common.dto.manager.v2.image.request import AliasImageInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.image.admin_alias(
                AliasImageInput(image_id=image_id, alias=alias_name)
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@alias.command(name="remove")
@click.argument("alias_name")
def alias_remove(alias_name: str) -> None:
    """Remove an image alias."""
    from ai.backend.common.dto.manager.v2.image.request import DealiasImageInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.image.admin_dealias(DealiasImageInput(alias=alias_name))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
