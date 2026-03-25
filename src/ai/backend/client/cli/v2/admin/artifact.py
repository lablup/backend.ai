"""Admin CLI commands for artifacts."""

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
def artifact() -> None:
    """Artifact admin commands."""


@artifact.command()
@click.option("--limit", default=None, type=int, help="Max results per page.")
@click.option("--offset", default=None, type=int, help="Pagination offset.")
@click.option(
    "--name-contains",
    default=None,
    type=str,
    help="Filter artifacts whose name contains this substring.",
)
@click.option(
    "--type",
    "artifact_type",
    default=None,
    type=str,
    help="Filter by artifact type (e.g., MODEL, PACKAGE, IMAGE).",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., NAME:asc, UPDATED_AT:desc).",
)
def search(
    limit: int | None,
    offset: int | None,
    name_contains: str | None,
    artifact_type: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search artifacts with admin scope."""
    from ai.backend.common.dto.manager.v2.artifact.request import (
        AdminSearchArtifactsInput,
        ArtifactFilter,
        ArtifactOrder,
    )
    from ai.backend.common.dto.manager.v2.artifact.types import ArtifactOrderField

    # Build filter only if any filter option is provided
    filter_dto: ArtifactFilter | None = None
    if name_contains is not None or artifact_type is not None:
        from ai.backend.common.dto.manager.query import StringFilter
        from ai.backend.common.dto.manager.v2.artifact.types import ArtifactType, ArtifactTypeFilter

        filter_dto = ArtifactFilter(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            type=ArtifactTypeFilter(equals=ArtifactType(artifact_type))
            if artifact_type is not None
            else None,
        )

    # Build order only if --order-by is provided
    orders = parse_order_options(order_by, ArtifactOrderField, ArtifactOrder) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.artifact.admin_search(
                AdminSearchArtifactsInput(
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
