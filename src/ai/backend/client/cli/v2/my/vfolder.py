"""CLI commands for self-service vfolder operations."""

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
def vfolder() -> None:
    """My vfolder commands."""


@vfolder.command(name="search-by-mount-permission")
@click.option("--domain", "domains", multiple=True, type=click.UUID, help="Domain ID (repeatable).")
@click.option(
    "--project", "projects", multiple=True, type=click.UUID, help="Project ID (repeatable)."
)
@click.option("--user", "users", multiple=True, type=click.UUID, help="User ID (repeatable).")
@click.option(
    "--mount-permission",
    "mount_permissions",
    multiple=True,
    required=True,
    type=click.Choice(["none", "ro", "rw"]),
    help="The level I mount the vfolder at (repeatable).",
)
@click.option("--name-contains", default=None, help="Filter by name substring.")
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option(
    "--order-by", multiple=True, help="Order by field:direction (e.g., name:asc, created_at:desc)."
)
def search_by_mount_permission(
    domains: tuple[UUID, ...],
    projects: tuple[UUID, ...],
    users: tuple[UUID, ...],
    mount_permissions: tuple[str, ...],
    name_contains: str | None,
    limit: int,
    offset: int,
    order_by: tuple[str, ...],
) -> None:
    """Search the vfolders of the named scopes by the level I mount them at."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
    from ai.backend.common.dto.manager.v2.vfolder.request import (
        ScopedSearchVFoldersByMountPermissionInput,
        VFolderFilter,
        VFolderOrder,
    )
    from ai.backend.common.dto.manager.v2.vfolder.types import (
        VFolderMountPermissionFilter,
        VFolderOrderField,
        VFolderPermissionField,
        VFolderScope,
    )

    if not domains and not projects and not users:
        raise click.UsageError("Name at least one of --domain, --project or --user.")
    request = ScopedSearchVFoldersByMountPermissionInput(
        scope=VFolderScope(
            domain=[UUIDScope(value=domain_id) for domain_id in domains] or None,
            project=[UUIDScope(value=project_id) for project_id in projects] or None,
            user=[UUIDScope(value=user_id) for user_id in users] or None,
        ),
        mount_permission=VFolderMountPermissionFilter(
            in_=[VFolderPermissionField(level) for level in mount_permissions]
        ),
        filter=(
            VFolderFilter(name=StringFilter(contains=name_contains))
            if name_contains is not None
            else None
        ),
        order=parse_order_options(order_by, VFolderOrderField, VFolderOrder) if order_by else None,
        limit=limit,
        offset=offset,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            print_result(await registry.vfolder.my_search_by_mount_permission(request))
        finally:
            await registry.close()

    asyncio.run(_run())
