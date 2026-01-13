from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from uuid import UUID

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

from .utils import bulk_insert_on_conflict_do_nothing

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


async def _insert_permission_groups(
    db_sess: SASession,
    role_ids: Collection[UUID],
    scope_id: ScopeId,
) -> None:
    """
    Ensure each role has a permission group for the given scope.

    When granting access to an entity, the target role needs a permission group
    for the entity's original scope to properly access it.
    """
    await bulk_insert_on_conflict_do_nothing(
        db_sess,
        [
            PermissionGroupRow(
                role_id=role_id,
                scope_type=scope_id.scope_type,
                scope_id=scope_id.scope_id,
            )
            for role_id in role_ids
        ],
    )


async def _insert_object_permissions(
    db_sess: SASession,
    role_ids: Collection[UUID],
    entity_id: ObjectId,
    operations: Collection[OperationType],
) -> None:
    """Insert object permissions for given roles, entity, and operations."""
    await bulk_insert_on_conflict_do_nothing(
        db_sess,
        [
            ObjectPermissionRow(
                role_id=role_id,
                entity_type=entity_id.entity_type,
                entity_id=entity_id.entity_id,
                operation=operation,
            )
            for role_id in role_ids
            for operation in operations
        ],
    )


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

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        granter: Granter instance containing granted_entity_id, target_role_ids, and operations.
    """
    role_ids = granter.target_role_ids
    entity_scope_id = granter.granted_entity_scope_id
    entity_id = granter.granted_entity_id

    if not role_ids:
        return

    # Grant permissions
    await _insert_permission_groups(db_sess, role_ids, entity_scope_id)
    await _insert_object_permissions(db_sess, role_ids, entity_id, granter.operations)
    await db_sess.flush()
