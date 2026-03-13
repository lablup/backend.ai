from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.permission.types import OperationType, ScopeType
from ai.backend.manager.data.permission.id import ObjectId
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow

# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class RBACRevoker:
    """
    Data class for revoking permissions from specific role(s).

    Uses entity-as-scope pattern: permissions are stored with scope_type/scope_id
    referring to the entity being revoked.

    Note: Only entity-level revoking is supported. Field-level revoking is not supported.

    Attributes:
        entity_id: The entity to revoke access from.
        entity_scope_type: The scope type for entity-as-scope in permissions table.
        target_role_ids: The role ID(s) to revoke permissions from.
        operations: Operations to revoke. If None, revokes all operations for the entity.
    """

    entity_id: ObjectId
    entity_scope_type: ScopeType
    target_role_ids: list[UUID]
    operations: list[OperationType] | None = None


# =============================================================================
# Deletion Helpers
# =============================================================================


async def _delete_permissions(
    db_sess: SASession,
    role_ids: Collection[UUID],
    entity_id: ObjectId,
    scope_type: ScopeType,
    operations: list[OperationType] | None,
) -> int:
    """Delete permissions for the given entity-as-scope and roles."""
    if not role_ids:
        return 0

    conditions = [
        PermissionRow.role_id.in_(role_ids),
        PermissionRow.scope_type == scope_type,
        PermissionRow.scope_id == entity_id.entity_id,
        PermissionRow.entity_type == entity_id.entity_type,
    ]

    if operations is not None:
        conditions.append(PermissionRow.operation.in_(operations))

    result = await db_sess.execute(sa.delete(PermissionRow).where(sa.and_(*conditions)))
    return cast(CursorResult[Any], result).rowcount or 0


# =============================================================================
# Public API
# =============================================================================


async def execute_rbac_revoker(
    db_sess: SASession,
    revoker: RBACRevoker,
) -> None:
    """
    Revoke permissions from specified roles using entity-as-scope pattern.

    This is used when unsharing an entity from specific roles.
    For example, when user A revokes user B's access to a VFolder:
    - User B's role loses permissions for that VFolder.

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        revoker: Revoker instance containing entity_id, entity_scope_type,
                 target_role_ids, and optional operations.
    """
    if not revoker.target_role_ids:
        return

    await _delete_permissions(
        db_sess,
        revoker.target_role_ids,
        revoker.entity_id,
        revoker.entity_scope_type,
        revoker.operations,
    )

    await db_sess.flush()
