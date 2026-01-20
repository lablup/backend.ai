from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from typing import cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import selectinload

from ai.backend.common.data.permission.types import OperationType
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.permission_group import PermissionGroupRow
from ai.backend.manager.models.rbac_models.role import RoleRow

# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class RBACRevoker:
    """
    Data class for revoking object-level permissions from specific role(s).

    Note: Only entity-level revoking is supported. Field-level revoking is not supported.

    Attributes:
        entity_id: The entity to revoke access from.
        target_role_ids: The role ID(s) to revoke permissions from.
        operations: Operations to revoke. If None, revokes all operations for the entity.
    """

    entity_id: ObjectId
    target_role_ids: list[UUID]
    operations: list[OperationType] | None = None


# =============================================================================
# Query Helpers
# =============================================================================


async def _get_roles_with_permissions(
    db_sess: SASession,
    role_ids: Collection[UUID],
) -> list[RoleRow]:
    """
    Get specified roles with their object permissions.

    Eagerly loads permission_groups and object_permissions to enable
    orphaned permission group detection.
    """
    if not role_ids:
        return []

    role_scalars = await db_sess.scalars(
        sa.select(RoleRow)
        .where(RoleRow.id.in_(role_ids))
        .options(
            selectinload(RoleRow.object_permission_rows).selectinload(
                ObjectPermissionRow.scope_association_rows
            ),
            selectinload(RoleRow.permission_group_rows).selectinload(
                PermissionGroupRow.permission_rows
            ),
        )
    )
    return list(role_scalars.unique().all())


# =============================================================================
# ID Collection Helpers (Pure Functions)
# =============================================================================


def _find_object_permissions_to_revoke(
    role_rows: Collection[RoleRow],
    entity_id: ObjectId,
    operations: list[OperationType] | None,
) -> list[UUID]:
    """
    Collect object permission IDs to revoke for the given entity and operations.

    Args:
        role_rows: Roles with loaded object_permissions
        entity_id: Entity to revoke permissions from
        operations: Operations to revoke. If None, revokes all operations.
    """
    object_permission_ids: list[UUID] = []
    for role_row in role_rows:
        for obj_perm in role_row.object_permission_rows:
            if obj_perm.object_id() != entity_id:
                continue
            if operations is None or obj_perm.operation in operations:
                object_permission_ids.append(obj_perm.id)
    return object_permission_ids


def _find_orphaned_perm_groups_after_revoke(
    role_rows: Collection[RoleRow],
    entity_id: ObjectId,
    operations_to_revoke: list[OperationType] | None,
) -> list[UUID]:
    """
    Identify permission_groups that will be orphaned after revoking permissions.

    A permission_group is orphaned if:
    1. It has no remaining PermissionRow entries, AND
    2. No other object_permission entity in this role belongs to the same scope
       (after the revoke operation)
    """
    perm_group_ids: list[UUID] = []

    for role_row in role_rows:
        if not role_row.permission_group_rows:
            continue

        # Determine which object permissions will remain after revoke
        remaining_scopes: set[ScopeId] = set()
        for obj_perm in role_row.object_permission_rows:
            # Check if this permission will be revoked
            if obj_perm.object_id() == entity_id:
                if operations_to_revoke is None or obj_perm.operation in operations_to_revoke:
                    continue  # This permission will be revoked
            # Collect scopes from remaining permissions
            for assoc in obj_perm.scope_association_rows:
                remaining_scopes.add(assoc.parsed_scope_id())

        # Check each permission group for orphan status
        for perm_group_row in role_row.permission_group_rows:
            # Skip if has remaining PermissionRows (type-level permissions)
            if perm_group_row.permission_rows:
                continue
            perm_group_scope = perm_group_row.parsed_scope_id()
            if perm_group_scope not in remaining_scopes:
                perm_group_ids.append(perm_group_row.id)

    return perm_group_ids


# =============================================================================
# Deletion Helpers
# =============================================================================


async def _delete_object_permissions(
    db_sess: SASession,
    ids: Collection[UUID],
) -> int:
    """Delete ObjectPermissionRows by IDs. Returns count of deleted rows."""
    if not ids:
        return 0
    result = await db_sess.execute(
        sa.delete(ObjectPermissionRow).where(ObjectPermissionRow.id.in_(ids))
    )
    return cast(CursorResult, result).rowcount or 0


async def _delete_orphan_permission_groups(
    db_sess: SASession,
    ids: Collection[UUID],
) -> int:
    """Delete PermissionGroupRows only if they have no remaining references.

    Uses NOT EXISTS to ensure no ObjectPermission or Permission references exist,
    preventing race conditions with concurrent Granter operations.
    """
    if not ids:
        return 0

    result = await db_sess.execute(
        sa.delete(PermissionGroupRow).where(
            sa.and_(
                PermissionGroupRow.id.in_(ids),
                ~sa.exists(
                    sa.select(ObjectPermissionRow.id).where(
                        ObjectPermissionRow.permission_group_id == PermissionGroupRow.id
                    )
                ),
                ~sa.exists(
                    sa.select(PermissionRow.id).where(
                        PermissionRow.permission_group_id == PermissionGroupRow.id
                    )
                ),
            )
        )
    )
    return cast(CursorResult, result).rowcount or 0


# =============================================================================
# Public API
# =============================================================================


async def execute_rbac_revoker(
    db_sess: SASession,
    revoker: RBACRevoker,
) -> None:
    """
    Revoke object-level permissions from specified roles.

    This is used when unsharing an entity from specific roles.
    For example, when user A revokes user B's access to a VFolder:
    - User B's role loses object permissions for that VFolder.
    - Orphaned permission groups are cleaned up.

    Deletion order (same as purger for safety):
    1. ObjectPermissionRows - permissions being revoked
    2. PermissionGroupRows - orphaned groups with no remaining permissions/entities

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        revoker: Revoker instance containing entity_id, target_role_ids, and optional operations.
    """
    if not revoker.target_role_ids:
        return

    # Collect related data with eager loading
    role_rows = await _get_roles_with_permissions(
        db_sess,
        revoker.target_role_ids,
    )

    # Find what to delete
    object_permission_ids = _find_object_permissions_to_revoke(
        role_rows,
        revoker.entity_id,
        revoker.operations,
    )
    permission_group_ids = _find_orphaned_perm_groups_after_revoke(
        role_rows,
        revoker.entity_id,
        revoker.operations,
    )

    # Execute deletions in order
    await _delete_object_permissions(db_sess, object_permission_ids)
    await _delete_orphan_permission_groups(db_sess, permission_group_ids)

    await db_sess.flush()
