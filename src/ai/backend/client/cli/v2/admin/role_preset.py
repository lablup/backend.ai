"""Admin CLI commands for the v2 role preset resource (superadmin only).

Delete is a soft-delete, Restore inverts it, and Purge is the hard delete.
Every active preset is auto-applied at scope creation, so there is no
``auto_apply`` argument on this surface.
"""

from __future__ import annotations

import uuid

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_model,
    load_v2_config,
    parse_order_options,
    print_result,
    run_async,
)


@click.group()
def role_preset() -> None:
    """Admin role preset commands (superadmin only)."""


@role_preset.command()
@click.option("--name", required=True, help="Role preset name.")
@click.option(
    "--scope-type",
    required=True,
    help="Scope type this preset targets (e.g., domain, project).",
)
@click.option(
    "--auto-assign/--no-auto-assign",
    default=False,
    help="Default auto-assign flag for roles instantiated from this preset.",
)
@click.option(
    "--permissions",
    default=None,
    help='Permission entries as JSON or @file: [{"entity_type": "...", "operation": "..."}].',
)
def create(
    name: str,
    scope_type: str,
    auto_assign: bool,
    permissions: str | None,
) -> None:
    """Create a new role preset."""
    from ai.backend.common.dto.manager.v2.rbac.types import RBACElementTypeDTO
    from ai.backend.common.dto.manager.v2.role_permission_preset.types import (
        RolePermissionPresetEntry,
    )
    from ai.backend.common.dto.manager.v2.role_preset.request import CreateRolePresetInput

    entries = (
        load_model(permissions, list[RolePermissionPresetEntry]) if permissions is not None else []
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.role_preset.create(
                CreateRolePresetInput(
                    name=name,
                    scope_type=RBACElementTypeDTO(scope_type),
                    auto_assign=auto_assign,
                    permissions=entries,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@role_preset.command()
@click.argument("role_preset_id", type=click.UUID)
def get(role_preset_id: uuid.UUID) -> None:
    """Get a single role preset by ID."""
    from ai.backend.common.identifier.role_preset import RolePresetID

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.role_preset.get(RolePresetID(role_preset_id))
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@role_preset.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--name-contains",
    default=None,
    help="Filter presets whose name contains this substring.",
)
@click.option("--scope-type", default=None, help="Filter by scope type.")
@click.option(
    "--auto-assign/--no-auto-assign",
    default=None,
    help="Filter by auto-assign flag.",
)
@click.option(
    "--deleted/--no-deleted",
    default=None,
    help="Filter by soft-delete flag (defaults to excluding soft-deleted rows).",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., name:asc, created_at:desc).",
)
def search(
    limit: int | None,
    offset: int | None,
    name_contains: str | None,
    scope_type: str | None,
    auto_assign: bool | None,
    deleted: bool | None,
    order_by: tuple[str, ...],
) -> None:
    """Search role presets across the system."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.rbac.types import RBACElementTypeDTO
    from ai.backend.common.dto.manager.v2.role_preset.request import (
        RolePresetFilter,
        RolePresetOrder,
        SearchRolePresetsInput,
    )
    from ai.backend.common.dto.manager.v2.role_preset.types import RolePresetOrderField

    filter_dto: RolePresetFilter | None = None
    if any(v is not None for v in (name_contains, scope_type, auto_assign, deleted)):
        filter_dto = RolePresetFilter(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            scope_type=RBACElementTypeDTO(scope_type) if scope_type is not None else None,
            auto_assign=auto_assign,
            deleted=deleted,
        )

    orders = (
        parse_order_options(order_by, RolePresetOrderField, RolePresetOrder) if order_by else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.role_preset.search(
                SearchRolePresetsInput(
                    filter=filter_dto,
                    order=orders,
                    limit=limit,
                    offset=offset,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@role_preset.command()
@click.argument("role_preset_id", type=click.UUID)
@click.option("--name", default=None, help="Updated name.")
@click.option(
    "--auto-assign/--no-auto-assign",
    default=None,
    help="Updated default auto-assign flag for instantiated roles.",
)
def update(
    role_preset_id: uuid.UUID,
    name: str | None,
    auto_assign: bool | None,
) -> None:
    """Update a role preset's mutable metadata."""
    from ai.backend.common.dto.manager.v2.role_preset.request import UpdateRolePresetBody
    from ai.backend.common.identifier.role_preset import RolePresetID

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.role_preset.update(
                RolePresetID(role_preset_id),
                UpdateRolePresetBody(name=name, auto_assign=auto_assign),
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@role_preset.command()
@click.argument("role_preset_ids", type=click.UUID, nargs=-1, required=True)
def delete(role_preset_ids: tuple[uuid.UUID, ...]) -> None:
    """Soft-delete one or more role presets (sets ``deleted = true``)."""
    from ai.backend.common.dto.manager.v2.role_preset.request import BulkDeleteRolePresetsInput
    from ai.backend.common.identifier.role_preset import RolePresetID

    ids = [RolePresetID(rid) for rid in role_preset_ids]

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.role_preset.delete(
                BulkDeleteRolePresetsInput(role_preset_ids=ids),
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@role_preset.command()
@click.argument("role_preset_ids", type=click.UUID, nargs=-1, required=True)
def restore(role_preset_ids: tuple[uuid.UUID, ...]) -> None:
    """Restore one or more soft-deleted role presets (sets ``deleted = false``)."""
    from ai.backend.common.dto.manager.v2.role_preset.request import BulkRestoreRolePresetsInput
    from ai.backend.common.identifier.role_preset import RolePresetID

    ids = [RolePresetID(rid) for rid in role_preset_ids]

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.role_preset.restore(
                BulkRestoreRolePresetsInput(role_preset_ids=ids),
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@role_preset.command()
@click.argument("role_preset_ids", type=click.UUID, nargs=-1, required=True)
def purge(role_preset_ids: tuple[uuid.UUID, ...]) -> None:
    """Hard-delete one or more role presets, cascading to their permission entries."""
    from ai.backend.common.dto.manager.v2.role_preset.request import BulkPurgeRolePresetsInput
    from ai.backend.common.identifier.role_preset import RolePresetID

    ids = [RolePresetID(rid) for rid in role_preset_ids]

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.role_preset.purge(
                BulkPurgeRolePresetsInput(role_preset_ids=ids),
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@role_preset.command(name="permission-search")
@click.argument("role_preset_id", type=click.UUID)
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option("--entity-type", default=None, help="Filter by entity type.")
@click.option("--operation", default=None, help="Filter by granted operation.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., entity_type:asc, created_at:desc).",
)
def permission_search(
    role_preset_id: uuid.UUID,
    limit: int | None,
    offset: int | None,
    entity_type: str | None,
    operation: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search the permission entries belonging to a single role preset."""
    from ai.backend.common.dto.manager.v2.rbac.types import (
        OperationTypeDTO,
        OperationTypeFilter,
        RBACElementTypeDTO,
        RBACElementTypeFilter,
    )
    from ai.backend.common.dto.manager.v2.role_permission_preset.request import (
        RolePermissionPresetFilter,
        RolePermissionPresetOrder,
        SearchRolePermissionPresetsInput,
    )
    from ai.backend.common.dto.manager.v2.role_permission_preset.types import (
        RolePermissionPresetOrderField,
    )
    from ai.backend.common.identifier.role_preset import RolePresetID

    filter_dto: RolePermissionPresetFilter | None = None
    if entity_type is not None or operation is not None:
        filter_dto = RolePermissionPresetFilter(
            entity_type=(
                RBACElementTypeFilter(equals=RBACElementTypeDTO(entity_type))
                if entity_type is not None
                else None
            ),
            operation=(
                OperationTypeFilter(equals=OperationTypeDTO(operation))
                if operation is not None
                else None
            ),
        )

    orders = (
        parse_order_options(order_by, RolePermissionPresetOrderField, RolePermissionPresetOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.role_preset.search_permissions(
                RolePresetID(role_preset_id),
                SearchRolePermissionPresetsInput(
                    filter=filter_dto,
                    order=orders,
                    limit=limit,
                    offset=offset,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@role_preset.command(name="permission-add")
@click.argument("role_preset_id", type=click.UUID)
@click.option(
    "--permissions",
    required=True,
    help='Permission entries as JSON or @file: [{"entity_type": "...", "operation": "..."}].',
)
def permission_add(role_preset_id: uuid.UUID, permissions: str) -> None:
    """Bulk-add permission entries to an existing role preset."""
    from ai.backend.common.dto.manager.v2.role_permission_preset.request import (
        BulkAddRolePermissionPresetsInput,
    )
    from ai.backend.common.dto.manager.v2.role_permission_preset.types import (
        RolePermissionPresetEntry,
    )
    from ai.backend.common.identifier.role_preset import RolePresetID

    entries = load_model(permissions, list[RolePermissionPresetEntry])

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.role_preset.add_permissions(
                RolePresetID(role_preset_id),
                BulkAddRolePermissionPresetsInput(permissions=entries),
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@role_preset.command(name="permission-remove")
@click.argument("permission_preset_ids", type=click.UUID, nargs=-1, required=True)
def permission_remove(permission_preset_ids: tuple[uuid.UUID, ...]) -> None:
    """Bulk-remove permission entries by their row IDs."""
    from ai.backend.common.dto.manager.v2.role_permission_preset.request import (
        BulkRemoveRolePermissionPresetsInput,
    )
    from ai.backend.common.identifier.role_permission_preset import RolePermissionPresetID

    ids = [RolePermissionPresetID(pid) for pid in permission_preset_ids]

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.role_preset.remove_permissions(
                BulkRemoveRolePermissionPresetsInput(permission_preset_ids=ids),
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)
