"""CLI commands for the v2 domain resource."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2.helpers import create_v2_registry, print_result


@click.group()
def domain() -> None:
    """Domain commands."""


@domain.command()
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
