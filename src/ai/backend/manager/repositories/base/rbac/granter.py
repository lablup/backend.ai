from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.permission.types import (
    OperationType,
)
from ai.backend.manager.data.permission.id import (
    ObjectId,
    ScopeId,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission_group import PermissionGroupRow

# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class RBACGranter:
    """
    Data class for granting object-level permissions to specific role(s).

    Note: Only entity-level granting is supported. Field-level granting is not supported.

    Attributes:
        granted_entity_id: The entity to grant access to (must be entity, not field).
        granted_entity_scope_id: The original scope where the entity belongs.
        target_role_ids: The role ID(s) to grant permissions to.
        operations: The operations to grant on the entity.
    """

    granted_entity_id: ObjectId
    granted_entity_scope_id: ScopeId
    target_role_ids: list[UUID]
    operations: list[OperationType]


# =============================================================================
# Insert Helpers
# =============================================================================


async def _upsert_permission_groups(
    db_sess: SASession,
    role_ids: Collection[UUID],
    scope_id: ScopeId,
) -> dict[UUID, UUID]:
    """
    Upsert permission groups for each role and return role_id -> permission_group_id mapping.

    Uses INSERT ... ON CONFLICT DO UPDATE ... RETURNING to atomically get IDs.
    """
    if not role_ids:
        return {}

    values_list = [
        {
            "role_id": role_id,
            "scope_type": scope_id.scope_type,
            "scope_id": scope_id.scope_id,
        }
        for role_id in role_ids
    ]

    stmt = (
        pg_insert(PermissionGroupRow)
        .values(values_list)
        .on_conflict_do_update(
            constraint="uq_permission_groups_role_scope",
            set_={
                "scope_type": sa.text("EXCLUDED.scope_type")
            },  # no-op update to trigger RETURNING
        )
        .returning(PermissionGroupRow.role_id, PermissionGroupRow.id)
    )

    result = await db_sess.execute(stmt)
    return {row.role_id: row.id for row in result.fetchall()}


async def _insert_object_permissions(
    db_sess: SASession,
    role_id_to_perm_group_id: dict[UUID, UUID],
    entity_id: ObjectId,
    operations: Collection[OperationType],
) -> None:
    """
    Insert object permissions with permission_group_id FK.

    Raises IntegrityError on unique constraint violation (duplicate permission).
    """
    if not role_id_to_perm_group_id or not operations:
        return

    obj_perms = [
        ObjectPermissionRow(
            role_id=role_id,
            permission_group_id=perm_group_id,
            entity_type=entity_id.entity_type,
            entity_id=entity_id.entity_id,
            operation=operation,
        )
        for role_id, perm_group_id in role_id_to_perm_group_id.items()
        for operation in operations
    ]
    db_sess.add_all(obj_perms)
    await db_sess.flush()


# =============================================================================
# Public API
# =============================================================================


async def execute_rbac_granter(
    db_sess: SASession,
    granter: RBACGranter,
) -> None:
    """
    Grant object-level permissions to specified roles.

    This is used when sharing an existing entity with specific roles.
    For example, when user A invites user B to a VFolder:
    - User B's role (provided by caller) gets object permissions for that VFolder.

    Flow:
    1. Upsert PermissionGroups and get their IDs
    2. Insert ObjectPermissions with permission_group_id FK

    Raises:
        IntegrityError: If duplicate object permission already exists.

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        granter: Granter instance containing granted_entity_id, target_role_ids, and operations.
    """
    role_ids = granter.target_role_ids
    entity_scope_id = granter.granted_entity_scope_id
    entity_id = granter.granted_entity_id

    if not role_ids:
        return

    # 1. Upsert permission groups and get IDs
    role_id_to_perm_group_id = await _upsert_permission_groups(db_sess, role_ids, entity_scope_id)

    # 2. Insert object permissions (raises on conflict)
    await _insert_object_permissions(
        db_sess, role_id_to_perm_group_id, entity_id, granter.operations
    )
