from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.permission.types import (
    OperationType,
)
from ai.backend.manager.data.permission.id import (
    ObjectId,
    ScopeId,
)
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission_group import PermissionGroupRow
from ai.backend.manager.models.rbac_models.role import RoleRow

from .utils import bulk_insert_on_conflict_do_nothing, insert_on_conflict_do_nothing

# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class RBACGranter:
    """
    Data class for granting object-level permissions to another scope.

    Note: Only entity-level granting is supported. Field-level granting is not supported.

    Attributes:
        granted_entity_id: The entity to grant access to (must be entity, not field).
        granted_entity_scope_id: The original scope where the entity belongs.
        target_scope_id: The scope to grant access to.
        operations: The operations to grant on the entity.
    """

    granted_entity_id: ObjectId
    granted_entity_scope_id: ScopeId
    target_scope_id: ScopeId
    operations: list[OperationType]


# =============================================================================
# Query Helpers
# =============================================================================


async def _find_system_roles_for_scope(
    db_sess: SASession,
    scope_id: ScopeId,
) -> list[RoleRow]:
    """Find system roles associated with the given scope via PermissionGroupRow."""
    result = await db_sess.scalars(
        sa.select(RoleRow)
        .select_from(sa.join(RoleRow, PermissionGroupRow, RoleRow.id == PermissionGroupRow.role_id))
        .where(
            sa.and_(
                RoleRow.source == RoleSource.SYSTEM,
                PermissionGroupRow.scope_id == scope_id.scope_id,
                PermissionGroupRow.scope_type == scope_id.scope_type,
            )
        )
    )
    return list(result.all())


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


async def _insert_scope_entity_association(
    db_sess: SASession,
    scope_id: ScopeId,
    entity_id: ObjectId,
) -> None:
    """Insert a scope-entity association to link the entity with the target scope."""
    await insert_on_conflict_do_nothing(
        db_sess,
        AssociationScopesEntitiesRow(
            scope_type=scope_id.scope_type,
            scope_id=scope_id.scope_id,
            entity_type=entity_id.entity_type,
            entity_id=entity_id.entity_id,
        ),
    )


# =============================================================================
# Public API
# =============================================================================


async def execute_rbac_granter(
    db_sess: SASession,
    granter: RBACGranter,
) -> None:
    """
    Grant object-level permissions to a scope's system roles.

    This is used when sharing an existing entity with another scope.
    For example, when user A invites user B to a VFolder:
    - User B's system role gets object permissions for that VFolder.
    - The VFolder is associated with user B's scope.

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        granter: Granter instance containing granted_entity_id, target_scope_id, and operations.
    """
    target_scope_id = granter.target_scope_id
    entity_scope_id = granter.granted_entity_scope_id
    entity_id = granter.granted_entity_id

    # Find system roles for the target scope
    system_roles = await _find_system_roles_for_scope(db_sess, target_scope_id)
    role_ids: list[UUID] = [role.id for role in system_roles]

    # Grant permissions
    await _insert_permission_groups(db_sess, role_ids, entity_scope_id)
    await _insert_object_permissions(db_sess, role_ids, entity_id, granter.operations)
    await _insert_scope_entity_association(db_sess, target_scope_id, entity_id)
    await db_sess.flush()
