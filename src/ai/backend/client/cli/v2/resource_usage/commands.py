"""CLI commands for resource usage management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2.helpers import create_v2_registry, print_result


@click.group()
def resource_usage() -> None:
    """Resource usage commands."""


@resource_usage.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option("--domain-name", default=None, help="Filter by domain name.")
@click.option("--resource-group", default=None, help="Filter by resource group.")
@pass_ctx_obj
def search_domain(
    ctx: CLIContext,
    limit: int | None,
    offset: int | None,
    domain_name: str | None,
    resource_group: str | None,
) -> None:
    """Search domain usage buckets."""
    from ai.backend.common.dto.manager.v2.resource_usage.request import (
        AdminSearchDomainUsageBucketsInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.resource_usage.search_domain_usage(
                AdminSearchDomainUsageBucketsInput(
                    limit=limit,
                    offset=offset,
                    domain_name=domain_name,
                    resource_group=resource_group,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_usage.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option("--domain-name", default=None, help="Filter by domain name.")
@click.option("--resource-group", default=None, help="Filter by resource group.")
@click.option("--project-id", default=None, help="Filter by project ID.")
@pass_ctx_obj
def search_project(
    ctx: CLIContext,
    limit: int | None,
    offset: int | None,
    domain_name: str | None,
    resource_group: str | None,
    project_id: str | None,
) -> None:
    """Search project usage buckets."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.resource_usage.request import (
        AdminSearchProjectUsageBucketsInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.resource_usage.search_project_usage(
                AdminSearchProjectUsageBucketsInput(
                    limit=limit,
                    offset=offset,
                    domain_name=domain_name,
                    resource_group=resource_group,
                    project_id=UUID(project_id) if project_id else None,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_usage.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option("--domain-name", default=None, help="Filter by domain name.")
@click.option("--resource-group", default=None, help="Filter by resource group.")
@click.option("--project-id", default=None, help="Filter by project ID.")
@click.option("--user-uuid", default=None, help="Filter by user UUID.")
@pass_ctx_obj
def search_user(
    ctx: CLIContext,
    limit: int | None,
    offset: int | None,
    domain_name: str | None,
    resource_group: str | None,
    project_id: str | None,
    user_uuid: str | None,
) -> None:
    """Search user usage buckets."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.resource_usage.request import (
        AdminSearchUserUsageBucketsInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.resource_usage.search_user_usage(
                AdminSearchUserUsageBucketsInput(
                    limit=limit,
                    offset=offset,
                    domain_name=domain_name,
                    resource_group=resource_group,
                    project_id=UUID(project_id) if project_id else None,
                    user_uuid=UUID(user_uuid) if user_uuid else None,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
