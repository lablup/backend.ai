"""CLI commands for self-service session operations."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config, print_result


@click.group()
def session() -> None:
    """My session commands."""


@session.command()
@click.option("--limit", default=None, type=int, help="Maximum number of results to return.")
@click.option("--offset", default=None, type=int, help="Number of results to skip.")
@click.option("--first", default=None, type=int, help="Cursor-based: return first N items.")
@click.option("--after", default=None, type=str, help="Cursor-based: return items after cursor.")
@click.option("--last", default=None, type=int, help="Cursor-based: return last N items.")
@click.option("--before", default=None, type=str, help="Cursor-based: return items before cursor.")
def search(
    limit: int | None,
    offset: int | None,
    first: int | None,
    after: str | None,
    last: int | None,
    before: str | None,
) -> None:
    """Search my sessions."""

    from ai.backend.common.dto.manager.v2.session.request import AdminSearchSessionsInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = AdminSearchSessionsInput(
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            )
            result = await registry.session.my_search(request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
