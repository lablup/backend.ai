"""CLI commands for self-service deployment operations."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config, print_result


@click.group()
def deployment() -> None:
    """My deployment commands."""


@deployment.command()
@click.option("--limit", default=None, type=int, help="Maximum number of results to return.")
@click.option("--offset", default=None, type=int, help="Number of results to skip.")
@click.option("--first", default=None, type=int, help="Cursor-based: return first N items.")
@click.option("--after", default=None, type=str, help="Cursor-based: return items after cursor.")
@click.option("--last", default=None, type=int, help="Cursor-based: return last N items.")
@click.option("--before", default=None, type=str, help="Cursor-based: return items before cursor.")
@click.option("--name-contains", default=None, type=str, help="Filter by name (contains).")
@click.option(
    "--status",
    multiple=True,
    help="Filter by status (repeatable, e.g., --status DEPLOYING --status READY).",
)
def search(
    limit: int | None,
    offset: int | None,
    first: int | None,
    after: str | None,
    last: int | None,
    before: str | None,
    name_contains: str | None,
    status: tuple[str, ...],
) -> None:
    """Search my deployments."""

    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.deployment.request import (
        AdminSearchDeploymentsInput,
        DeploymentFilter,
        DeploymentStatusFilter,
    )

    filter_dto: DeploymentFilter | None = None
    if name_contains or status:
        filter_dto = DeploymentFilter(
            name=StringFilter(contains=name_contains) if name_contains else None,
            status=DeploymentStatusFilter(in_=list(status)) if status else None,
        )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = AdminSearchDeploymentsInput(
                filter=filter_dto,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            )
            result = await registry.deployment.my_search(request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
