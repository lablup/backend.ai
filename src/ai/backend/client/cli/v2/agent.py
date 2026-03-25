"""CLI commands for the v2 agent resource."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2._helpers import create_v2_registry, print_result


@click.group()
def agents() -> None:
    """Agent management commands."""


@agents.command()
@pass_ctx_obj
@click.option("--limit", default=20, help="Maximum number of results to return.")
@click.option("--offset", default=0, help="Number of results to skip.")
def search(ctx: CLIContext, limit: int, offset: int) -> None:
    """Search agents (superadmin only)."""
    from ai.backend.common.dto.manager.v2.agent.request import AdminSearchAgentsInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.agent.admin_search(
                AdminSearchAgentsInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@agents.command(name="total-resources")
@pass_ctx_obj
def total_resources(ctx: CLIContext) -> None:
    """Get aggregate resource statistics across all agents (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.agent.get_total_resources()
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
