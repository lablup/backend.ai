"""CLI commands for the v2 container registry domain.

Admin-only commands (search) are under ``admin container-registry``.
"""

from __future__ import annotations

from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
    run_async,
)


@click.group(name="container-registry")
def container_registry() -> None:
    """Container registry management commands."""


@container_registry.command(name="scoped-search")
@click.option(
    "--domain",
    "domain_ids",
    type=click.UUID,
    multiple=True,
    required=True,
    help="Domain whose related registries are read (repeatable; OR across every domain).",
)
@click.option("--limit", type=int, default=None, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--registry-name",
    default=None,
    type=str,
    help="Filter registries whose name contains this substring.",
)
@click.option(
    "--type",
    "registry_type",
    default=None,
    type=str,
    help="Filter by registry type (e.g., docker, harbor, harbor2).",
)
@click.option(
    "--is-global/--no-is-global",
    default=None,
    help="Filter by global accessibility.",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., registry_name:asc, type:desc).",
)
def scoped_search(
    domain_ids: tuple[UUID, ...],
    limit: int | None,
    offset: int | None,
    registry_name: str | None,
    registry_type: str | None,
    is_global: bool | None,
    order_by: tuple[str, ...],
) -> None:
    """Search the container registries the given domains are related to."""
    from ai.backend.common.container_registry import ContainerRegistryType
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.container_registry.request import (
        ContainerRegistryFilter,
        ContainerRegistryOrder,
        ScopedSearchContainerRegistriesInput,
    )
    from ai.backend.common.dto.manager.v2.container_registry.types import (
        ContainerRegistryOrderField,
        ContainerRegistryScope,
        ContainerRegistryTypeFilter,
    )
    from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope

    registry_filter: ContainerRegistryFilter | None = None
    if registry_name is not None or registry_type is not None or is_global is not None:
        registry_filter = ContainerRegistryFilter(
            registry_name=StringFilter(contains=registry_name)
            if registry_name is not None
            else None,
            type=ContainerRegistryTypeFilter(equals=ContainerRegistryType(registry_type))
            if registry_type is not None
            else None,
            is_global=is_global,
        )
    orders = (
        parse_order_options(order_by, ContainerRegistryOrderField, ContainerRegistryOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.container_registry.scoped_search(
                ScopedSearchContainerRegistriesInput(
                    scope=ContainerRegistryScope(
                        domain=[UUIDScope(value=domain_id) for domain_id in domain_ids]
                    ),
                    filter=registry_filter,
                    order=orders,
                    limit=limit,
                    offset=offset,
                )
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)
