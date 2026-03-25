"""CLI commands for the v2 domain resource."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2.helpers import create_v2_registry, print_result


@click.group()
def domains() -> None:
    """Domain management commands."""


@domains.command()
@pass_ctx_obj
@click.option("--limit", default=20, help="Maximum number of results to return.")
@click.option("--offset", default=0, help="Number of results to skip.")
def search(ctx: CLIContext, limit: int, offset: int) -> None:
    """Search domains."""
    from ai.backend.common.dto.manager.v2.domain.request import AdminSearchDomainsInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.domain.admin_search(
                AdminSearchDomainsInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@domains.command()
@pass_ctx_obj
@click.argument("domain_name")
def get(ctx: CLIContext, domain_name: str) -> None:
    """Get a domain by name."""

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.domain.get(domain_name)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
