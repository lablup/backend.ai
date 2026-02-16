from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.permission.types import (
    OperationType,
    RelationType,
    ScopeType,
)
from ai.backend.manager.data.permission.id import (
    ObjectId,
    ScopeId,
)
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow

# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class RBACGranter:
    """
    Data class for granting permissions to specific role(s) using entity-as-scope pattern.

    This performs two operations:
    1. Insert a ref edge in association_scopes_entities (visibility).
    2. Insert entity-scope permissions in the permissions table (access control).

    Note: Only entity-level granting is supported. Field-level granting is not supported.

    Attributes:
        granted_entity_id: The entity to grant access to (must be entity, not field).
        granted_entity_scope_type: The scope_type for entity-as-scope in permissions table.
        target_scope_id: The scope to associate the entity with (e.g., invitee's User scope).
        target_role_ids: The role ID(s) to grant permissions to.
        operations: The operations to grant on the entity.
    """

    granted_entity_id: ObjectId
    granted_entity_scope_type: ScopeType
    target_scope_id: ScopeId
    target_role_ids: list[UUID]
    operations: list[OperationType]


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

    if not role_ids or not granter.operations:
        return

    # 1. Insert ref edge in association_scopes_entities (visibility)
    db_sess.add(
        AssociationScopesEntitiesRow(
            scope_type=granter.target_scope_id.scope_type,
            scope_id=granter.target_scope_id.scope_id,
            entity_type=entity_id.entity_type,
            entity_id=entity_id.entity_id,
            relation_type=RelationType.REF,
        )
    )

    # 2. Insert entity-scope permissions (access control)
    perms = [
        PermissionRow(
            role_id=role_id,
            scope_type=granter.granted_entity_scope_type,
            scope_id=entity_id.entity_id,
            entity_type=entity_id.entity_type,
            operation=operation,
        )
        for role_id in role_ids
        for operation in granter.operations
    ]
    db_sess.add_all(perms)
    await db_sess.flush()
