"""CLI commands for project fair share."""

from __future__ import annotations

import asyncio
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group()
def project() -> None:
    """Project fair share commands."""


@project.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option("--resource-group", default=None, type=str, help="Filter by resource group name.")
@click.option("--domain-name", default=None, type=str, help="Filter by domain name.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., fair_share_factor:desc, project_name:asc).",
)
def search(
    limit: int | None,
    offset: int | None,
    resource_group: str | None,
    domain_name: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search project fair shares."""
    from ai.backend.common.dto.manager.v2.fair_share.request import (
        ProjectFairShareFilter,
        ProjectFairShareOrder,
        SearchProjectFairSharesInput,
    )
    from ai.backend.common.dto.manager.v2.fair_share.types import ProjectFairShareOrderField

    # Build filter only if any filter option is provided
    filter_dto: ProjectFairShareFilter | None = None
    if resource_group is not None or domain_name is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = ProjectFairShareFilter(
            resource_group=StringFilter(contains=resource_group)
            if resource_group is not None
            else None,
            domain_name=StringFilter(contains=domain_name) if domain_name is not None else None,
        )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, ProjectFairShareOrderField, ProjectFairShareOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.fair_share.search_project(
                SearchProjectFairSharesInput(
                    filter=filter_dto,
                    order=orders,
                    limit=limit,
                    offset=offset,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@project.command()
@click.option("--resource-group", type=str, help="Resource group name.")
@click.option("--resource-group-id", type=click.UUID, help="Resource group ID.")
@click.option("--project-id", required=True, type=click.UUID, help="Project UUID.")
def get(resource_group: str | None, resource_group_id: UUID | None, project_id: UUID) -> None:
    """Get a single project fair share record."""
    from ai.backend.common.dto.manager.v2.fair_share.request import GetProjectFairShareInput
    from ai.backend.common.identifier.resource_group import ResourceGroupID

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            resolved_resource_group_id: ResourceGroupID
            if resource_group_id is not None:
                resolved_resource_group_id = ResourceGroupID(resource_group_id)
            elif resource_group is not None:
                result = await registry.resource_group.get(resource_group)
                resolved_resource_group_id = ResourceGroupID(result.resource_group_id)
            else:
                raise click.UsageError("--resource-group or --resource-group-id is required.")
            result = await registry.fair_share.get_project(
                GetProjectFairShareInput(
                    resource_group_id=resolved_resource_group_id,
                    project_id=project_id,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
