from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.permission.types import (
    OperationType,
    ScopeType,
)
from ai.backend.manager.data.permission.id import (
    ObjectId,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow

# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class RBACGranter:
    """
    Data class for granting permissions to specific role(s) using entity-as-scope pattern.

    Note: Only entity-level granting is supported. Field-level granting is not supported.

    Attributes:
        granted_entity_id: The entity to grant access to (must be entity, not field).
        granted_entity_scope_type: The scope_type for entity-as-scope in permissions table.
        target_role_ids: The role ID(s) to grant permissions to.
        operations: The operations to grant on the entity.
    """

    granted_entity_id: ObjectId
    granted_entity_scope_type: ScopeType
    target_role_ids: list[UUID]
    operations: list[OperationType]


# =============================================================================
# Insert Helpers
# =============================================================================


async def _insert_permissions(
    db_sess: SASession,
    role_ids: Collection[UUID],
    entity_id: ObjectId,
    scope_type: ScopeType,
    operations: Collection[OperationType],
) -> None:
    """
    Insert permissions for each role using entity-as-scope pattern.

    Raises IntegrityError on unique constraint violation (duplicate permission).
    """
    if not role_ids or not operations:
        return

    perms = [
        PermissionRow(
            role_id=role_id,
            scope_type=scope_type,
            scope_id=entity_id.entity_id,
            entity_type=entity_id.entity_type,
            operation=operation,
        )
        for role_id in role_ids
        for operation in operations
    ]
    db_sess.add_all(perms)
    await db_sess.flush()


# =============================================================================
# Public API
# =============================================================================


async def execute_rbac_granter(
    db_sess: SASession,
    granter: RBACGranter,
) -> None:
    """
    Grant permissions to specified roles using entity-as-scope pattern.

    This is used when sharing an existing entity with specific roles.
    For example, when user A invites user B to a VFolder:
    - User B's role (provided by caller) gets permissions for that VFolder.

    Raises:
        IntegrityError: If duplicate permission already exists.

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        granter: Granter instance containing granted_entity_id, target_role_ids, and operations.
    """
    role_ids = granter.target_role_ids
    entity_id = granter.granted_entity_id

    if not role_ids:
        return

    # Insert permissions (raises on conflict)
    await _insert_permissions(
        db_sess, role_ids, entity_id, granter.granted_entity_scope_type, granter.operations
    )
