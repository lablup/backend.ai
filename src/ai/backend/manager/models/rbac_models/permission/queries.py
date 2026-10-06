"""Effective entity permissions shared by RBAC checks and filtered searches."""

from __future__ import annotations

import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import EntityMembershipCapRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow


def owned_permission_query(
    user_id: UserID, entity_type: EntityType, subject_entity_type: EntityType
) -> sa.Select[tuple[uuid.UUID, int]]:
    """Resolve all-field permissions through ownership, roles, and share/govern caps."""
    own = EntityMembershipRow.__table__
    share_cap = EntityMembershipCapRow.__table__
    govern = ScopeBindingRow.__table__
    entity = VirtualEntityRow.__table__.alias("entity")
    governor = VirtualEntityRow.__table__.alias("governor")
    perm = PermissionRow.__table__
    roles = RoleRow.__table__
    user_roles = UserRoleRow.__table__

    full_cap = int(Permission.full())
    # entity <- own - ve <- govern - governor <- permission <- role <- user; one row
    # per entity, the paths OR-ed in SQL after each is clipped by its govern cap.
    return (
        sa.select(
            entity.c.entity_id,
            sa.func.bit_or(
                perm.c.permission.op("&")(sa.func.coalesce(govern.c.permission_cap, full_cap))
            ).label("granted"),
        )
        .select_from(
            own.join(entity, entity.c.id == own.c.member_entity_id)
            .join(govern, govern.c.virtual_entity_id == own.c.virtual_entity_id)
            .join(governor, governor.c.id == govern.c.scope_entity_id)
            .join(
                roles,
                sa.and_(
                    roles.c.scope_type == governor.c.entity_type,
                    roles.c.scope_id == governor.c.entity_id,
                ),
            )
            .join(
                perm,
                sa.and_(
                    perm.c.role_id == roles.c.id,
                    perm.c.entity_type == subject_entity_type,
                    perm.c.all_fields.is_(True),
                ),
            )
            .join(user_roles, user_roles.c.role_id == roles.c.id)
            .outerjoin(
                share_cap,
                sa.and_(
                    share_cap.c.membership_id == own.c.id,
                    share_cap.c.permission == perm.c.permission,
                    share_cap.c.all_fields.is_(True),
                ),
            )
        )
        .where(
            entity.c.entity_type == entity_type,
            user_roles.c.user_id == user_id,
            roles.c.status == RoleStatus.ACTIVE,
            # Own reaches every governor; a share requires an all-field cap for
            # this bit and reaches only its own governor and entity type.
            sa.or_(
                own.c.capped.is_(False),
                sa.and_(
                    share_cap.c.id.is_not(None),
                    entity.c.entity_type == subject_entity_type,
                    govern.c.scope_entity_id == govern.c.virtual_entity_id,
                ),
            ),
        )
        .group_by(entity.c.entity_id)
    )


def entity_read_permission(
    user_id: UserID,
    entity_type: EntityType,
    entity_id: sa.ColumnElement[Any] | InstrumentedAttribute[Any],
) -> sa.ColumnElement[bool]:
    """Filter unreadable entities before pagination; superadmins bypass the check."""
    granted = owned_permission_query(user_id, entity_type, entity_type).subquery()
    readable = sa.select(granted.c.entity_id).where(
        granted.c.granted.op("&")(int(Permission.READ)) == int(Permission.READ)
    )
    superadmin = sa.exists(
        sa.select(1).where(UserRow.uuid == user_id, UserRow.role == UserRole.SUPERADMIN)
    )
    return sa.or_(superadmin, entity_id.in_(readable))
