from __future__ import annotations

from dataclasses import dataclass

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


@dataclass
class Inviter:
    entity_id: ObjectId
    scope_id: ScopeId
    operations: list[OperationType]


async def execute_inviter(
    db_sess: SASession,
    inviter: Inviter,
) -> None:
    scope_id = inviter.scope_id
    object_id = inviter.entity_id

    scope_system_roles = await db_sess.scalars(
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
    role_ids = [role.id for role in scope_system_roles.all()]
    for role_id in role_ids:
        for operation in inviter.operations:
            db_sess.add(
                ObjectPermissionRow(
                    role_id=role_id,
                    entity_type=object_id.entity_type,
                    entity_id=object_id.entity_id,
                    operation=operation,
                )
            )
    db_sess.add(
        AssociationScopesEntitiesRow(
            scope_type=scope_id.scope_type,
            scope_id=scope_id.scope_id,
            entity_type=object_id.entity_type,
            entity_id=object_id.entity_id,
        )
    )
