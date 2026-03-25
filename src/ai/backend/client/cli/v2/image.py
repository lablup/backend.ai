"""CLI commands for the v2 image domain."""

from __future__ import annotations

import asyncio
from typing import Any

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2._helpers import create_v2_registry, print_result


@click.group()
def images() -> None:
    """Image management commands."""


@images.command()
@pass_ctx_obj
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option("--filter", "filter_json", default=None, help="JSON filter expression.")
def search(ctx: CLIContext, limit: int, offset: int, filter_json: str | None) -> None:
    """Search images with admin scope."""
    from ai.backend.common.dto.manager.v2.image.request import AdminSearchImagesInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            kwargs: dict[str, Any] = {"limit": limit, "offset": offset}
            if filter_json is not None:
                import json

                kwargs["filter"] = json.loads(filter_json)
            request = AdminSearchImagesInput(**kwargs)
            result = await registry.image.admin_search(request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@images.command(name="search-aliases")
@pass_ctx_obj
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option("--filter", "filter_json", default=None, help="JSON filter expression.")
def search_aliases(ctx: CLIContext, limit: int, offset: int, filter_json: str | None) -> None:
    """Search image aliases with admin scope."""
    from ai.backend.common.dto.manager.v2.image.request import AdminSearchImageAliasesInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            kwargs: dict[str, Any] = {"limit": limit, "offset": offset}
            if filter_json is not None:
                import json

                kwargs["filter"] = json.loads(filter_json)
            request = AdminSearchImageAliasesInput(**kwargs)
            result = await registry.image.admin_search_image_aliases(request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
