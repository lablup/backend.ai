from __future__ import annotations

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


@dataclass
class Granter:
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


async def _find_system_roles_for_scope(
    db_sess: SASession,
    scope_id: ScopeId,
) -> list[RoleRow]:
    """
    Find system roles associated with the given scope via PermissionGroupRow.
    """
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
    return result.all()


async def _ensure_entity_scope_permission_group(
    db_sess: SASession,
    role_ids: list[UUID],
    entity_scope_id: ScopeId,
) -> None:
    """
    Ensure each role has a permission group for the granted entity's original scope.

    When granting access to an entity, the target role needs a permission group
    for the entity's original scope to properly access it.

    Args:
        db_sess: Async SQLAlchemy session.
        role_ids: List of role IDs to ensure permission groups for.
        entity_scope_id: The original scope of the granted entity.
    """
    await bulk_insert_on_conflict_do_nothing(
        db_sess,
        [
            PermissionGroupRow(
                role_id=role_id,
                scope_type=entity_scope_id.scope_type,
                scope_id=entity_scope_id.scope_id,
            )
            for role_id in role_ids
        ],
    )


async def _add_object_permissions(
    db_sess: SASession,
    role_ids: list[UUID],
    entity_id: ObjectId,
    operations: list[OperationType],
) -> None:
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


async def _add_scope_entity_association(
    db_sess: SASession,
    target_scope_id: ScopeId,
    entity_id: ObjectId,
) -> None:
    await insert_on_conflict_do_nothing(
        db_sess,
        AssociationScopesEntitiesRow(
            scope_type=target_scope_id.scope_type,
            scope_id=target_scope_id.scope_id,
            entity_type=entity_id.entity_type,
            entity_id=entity_id.entity_id,
        ),
    )


async def execute_granter(
    db_sess: SASession,
    granter: Granter,
) -> None:
    """
    Grant object-level permissions to a scope's system roles.

    This is used when sharing an existing entity with another scope.
    For example, when user A invites user B to a VFolder:
    - User B's system role gets object permissions for that VFolder.
    - The VFolder is associated with user B's scope.

    Args:
        db_sess: Async SQLAlchemy session.
        granter: Granter instance containing granted_entity_id, target_scope_id, and operations.
    """
    target_scope_id = granter.target_scope_id

    entity_scope_id = granter.granted_entity_scope_id
    entity_id = granter.granted_entity_id

    # Find system roles for this scope
    system_roles = await _find_system_roles_for_scope(db_sess, target_scope_id)
    role_ids: list[UUID] = [role.id for role in system_roles]

    await _ensure_entity_scope_permission_group(
        db_sess,
        role_ids,
        entity_scope_id,
    )
    await _add_object_permissions(
        db_sess,
        role_ids,
        entity_id,
        granter.operations,
    )
    await _add_scope_entity_association(
        db_sess,
        target_scope_id,
        entity_id,
    )
    await db_sess.flush()
