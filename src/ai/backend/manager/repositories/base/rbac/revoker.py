from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import selectinload

from ai.backend.common.data.permission.types import OperationType
from ai.backend.manager.data.permission.id import ObjectId
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
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
    return cast(CursorResult[Any], result).rowcount or 0


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

    Deletion order:
    1. ObjectPermissionRows - permissions being revoked

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

    # Execute deletions
    await _delete_object_permissions(db_sess, object_permission_ids)

    await db_sess.flush()
