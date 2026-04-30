"""CLI commands for RBAC role management."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)

if TYPE_CHECKING:
    from ai.backend.client.v2.v2_registry import V2ClientRegistry


@click.group()
def role() -> None:
    """RBAC role commands."""


@role.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., name:asc, created_at:desc).",
)
@click.option("--name-contains", type=str, default=None, help="Filter roles by name (contains).")
@click.option(
    "--source",
    type=click.Choice(["system", "custom"], case_sensitive=False),
    default=None,
    help="Filter by role source.",
)
@click.option(
    "--status",
    type=click.Choice(["active", "inactive", "deleted"], case_sensitive=False),
    default=None,
    help="Filter by role status.",
)
def search(
    limit: int | None,
    offset: int | None,
    order_by: tuple[str, ...],
    name_contains: str | None,
    source: str | None,
    status: str | None,
) -> None:
    """Search roles."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.rbac.request import (
        RoleFilter,
        RoleOrderBy,
        SearchRolesInput,
    )
    from ai.backend.common.dto.manager.v2.rbac.types import (
        RoleOrderField,
        RoleSourceFilter,
        RoleStatusFilter,
    )

    # Build filter only if any filter option is provided
    filter_dto: RoleFilter | None = None
    if any([name_contains is not None, source is not None, status is not None]):
        filter_dto = RoleFilter(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            source=RoleSourceFilter(equals=source) if source is not None else None,
            status=RoleStatusFilter(equals=status) if status is not None else None,
        )

    # Build order only if --order-by is provided
    orders = parse_order_options(order_by, RoleOrderField, RoleOrderBy) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.rbac.search_roles(
                SearchRolesInput(
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


@role.command(name="project-search")
@click.argument("project_id", type=str)
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., name:asc, created_at:desc).",
)
@click.option("--name-contains", type=str, default=None, help="Filter roles by name (contains).")
@click.option(
    "--source",
    type=click.Choice(["system", "custom"], case_sensitive=False),
    default=None,
    help="Filter by role source.",
)
@click.option(
    "--status",
    type=click.Choice(["active", "inactive", "deleted"], case_sensitive=False),
    default=None,
    help="Filter by role status.",
)
def project_search(
    project_id: str,
    limit: int | None,
    offset: int | None,
    order_by: tuple[str, ...],
    name_contains: str | None,
    source: str | None,
    status: str | None,
) -> None:
    """Search roles registered in a project scope."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.rbac.request import (
        RoleFilter,
        RoleOrderBy,
        SearchRolesInput,
    )
    from ai.backend.common.dto.manager.v2.rbac.types import (
        RoleOrderField,
        RoleSourceFilter,
        RoleStatusFilter,
    )

    filter_dto: RoleFilter | None = None
    if any([name_contains is not None, source is not None, status is not None]):
        filter_dto = RoleFilter(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            source=RoleSourceFilter(equals=source) if source is not None else None,
            status=RoleStatusFilter(equals=status) if status is not None else None,
        )

    orders = parse_order_options(order_by, RoleOrderField, RoleOrderBy) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.rbac.project_search_roles(
                UUID(project_id),
                SearchRolesInput(
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


@role.command()
@click.argument("role_id", type=str)
def get(role_id: str) -> None:
    """Get a role by UUID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.rbac.get_role(UUID(role_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@role.command()
@click.option("--name", required=True, help="Role name.")
@click.option("--description", default=None, help="Role description.")
def create(name: str, description: str | None) -> None:
    """Create a new role."""
    from ai.backend.common.dto.manager.v2.rbac.request import CreateRoleInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.rbac.create_role(
                CreateRoleInput(name=name, description=description),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@role.command()
@click.argument("role_id", type=str)
def delete(role_id: str) -> None:
    """Soft-delete a role."""
    from ai.backend.common.dto.manager.v2.rbac.request import DeleteRoleInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.rbac.delete_role(
                DeleteRoleInput(id=UUID(role_id)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


def _validate_role_selector(role_id: UUID | None, by_name: str | None) -> None:
    if not role_id and not by_name:
        raise click.UsageError("Provide ROLE_ID or --by-name.")
    if role_id and by_name:
        raise click.UsageError("ROLE_ID and --by-name are mutually exclusive.")


async def _resolve_role_id(
    registry: V2ClientRegistry,
    role_id: UUID | None,
    by_name: str | None,
) -> UUID:
    if role_id is not None:
        return role_id
    if by_name is None:
        raise click.UsageError("Provide ROLE_ID or --by-name.")
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.rbac.request import RoleFilter, SearchRolesInput

    payload = await registry.rbac.search_roles(
        SearchRolesInput(filter=RoleFilter(name=StringFilter(equals=by_name))),
    )
    items = payload.items
    if not items:
        raise click.ClickException(f"No role matches name {by_name!r}.")
    if len(items) == 1:
        return items[0].id
    click.echo(f"Multiple roles match {by_name!r}:")
    for i, role_node in enumerate(items, start=1):
        click.echo(
            f"  [{i}] {role_node.id}  name={role_node.name}  "
            f"source={role_node.source}  status={role_node.status}",
        )
    if not sys.stdin.isatty():
        raise click.ClickException(
            f"{len(items)} roles match name {by_name!r}; "
            f"re-run with ROLE_ID positional argument or in an interactive shell.",
        )
    choice: int = click.prompt("Select role number", type=click.IntRange(1, len(items)))
    return items[choice - 1].id


@role.command(name="add-permission")
@click.argument("role_id", type=click.UUID, required=False)
@click.option("--by-name", type=str, default=None, help="Resolve role by name.")
@click.option(
    "--kind",
    type=click.Choice(["admin", "owner", "member"]),
    required=True,
    help="Operation set kind to grant on every resource entity type.",
)
def add_permission(role_id: UUID | None, by_name: str | None, kind: str) -> None:
    """Add the standard <kind> permissions for every resource entity type to a role."""
    _validate_role_selector(role_id, by_name)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            resolved = await _resolve_role_id(registry, role_id, by_name)
            raise click.ClickException(
                f"Not yet wired to SDK (BA-5912 pending): role_id={resolved}, kind={kind!r}.",
            )
        finally:
            await registry.close()

    asyncio.run(_run())


@role.command(name="remove-permission")
@click.argument("role_id", type=click.UUID, required=False)
@click.option("--by-name", type=str, default=None, help="Resolve role by name.")
@click.option(
    "--kind",
    type=click.Choice(["admin", "owner", "member"]),
    required=True,
    help="Operation set kind to revoke.",
)
def remove_permission(
    role_id: UUID | None,
    by_name: str | None,
    kind: str,
) -> None:
    """Remove the standard <kind> permissions for every resource entity type from a role."""
    _validate_role_selector(role_id, by_name)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            resolved = await _resolve_role_id(registry, role_id, by_name)
            raise click.ClickException(
                f"Not yet wired to SDK (BA-5912 pending): role_id={resolved}, kind={kind!r}.",
            )
        finally:
            await registry.close()

    asyncio.run(_run())


@role.command(name="replace-permission")
@click.argument("role_id", type=click.UUID, required=False)
@click.option("--by-name", type=str, default=None, help="Resolve role by name.")
@click.option(
    "--json",
    "json_str",
    type=str,
    default=None,
    help="Permission entries as a JSON-array string. Mutually exclusive with --from-file.",
)
@click.option(
    "--from-file",
    "file_path",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    default=None,
    help="Path to a file containing permission entries as a JSON array.",
)
def replace_permission(
    role_id: UUID | None,
    by_name: str | None,
    json_str: str | None,
    file_path: Path | None,
) -> None:
    """Replace the role's entire permission set with the entries supplied via --json or --from-file."""
    _validate_role_selector(role_id, by_name)
    if json_str is not None and file_path is not None:
        raise click.UsageError("--json and --from-file are mutually exclusive.")
    if json_str is None and file_path is None:
        raise click.UsageError("Provide --json or --from-file.")

    raw = file_path.read_text() if file_path is not None else json_str
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Failed to parse permission entries as JSON: {e}") from e
    if not isinstance(payload, list):
        raise click.UsageError("Payload must be a JSON array of permission entries.")

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            resolved = await _resolve_role_id(registry, role_id, by_name)
            raise click.ClickException(
                f"Not yet wired to SDK (BA-5912 pending): "
                f"role_id={resolved}, entries={len(payload)}.",
            )
        finally:
            await registry.close()

    asyncio.run(_run())
