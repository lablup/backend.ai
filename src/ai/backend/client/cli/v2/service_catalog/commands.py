"""CLI commands for the v2 service catalog domain."""

from __future__ import annotations

import asyncio
from typing import Any

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2.helpers import create_v2_registry, print_result


@click.group()
def service_catalogs() -> None:
    """Service catalog management commands."""


@service_catalogs.command()
@pass_ctx_obj
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option("--filter", "filter_json", default=None, help="JSON filter expression.")
def search(ctx: CLIContext, limit: int, offset: int, filter_json: str | None) -> None:
    """Search service catalog entries with admin scope."""
    from ai.backend.common.dto.manager.v2.service_catalog.request import (
        AdminSearchServiceCatalogsInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            kwargs: dict[str, Any] = {"limit": limit, "offset": offset}
            if filter_json is not None:
                import json

                kwargs["filter"] = json.loads(filter_json)
            request = AdminSearchServiceCatalogsInput(**kwargs)
            result = await registry.service_catalog.admin_search(request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
