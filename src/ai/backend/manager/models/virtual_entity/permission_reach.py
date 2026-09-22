"""What a user's roles reach, as a predicate a search can be narrowed to.

The span is the one the permission check walks in
``repositories/ops/v2/permission/read.py``: ``entity <- own - ve <- govern - scope <-
role <- user``, with the role's bits clipped by the govern cap and the share cap. A row
this predicate keeps is therefore a row the check answers for.

A superadmin holds every bit without a role, so their read is unscoped and never reaches
here.
"""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import EntityMembershipCapRow
from ai.backend.manager.models.virtual_entity.queries import UuidExpr
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow

__all__ = ("user_permission_reaches",)


def user_permission_reaches(
    user_id: UuidExpr,
    permission: Permission,
    entity_type: EntityType,
    entity_id: UuidExpr,
) -> sa.ColumnElement[bool]:
    """EXISTS predicate: a role the user holds grants ``permission`` on the entity.

    Every scope the user holds a role in answers, so one scope granting nothing leaves
    the others standing. Either id accepts a literal UUID or a column expression, so the
    predicate works both as a direct filter and as a correlated condition.
    """
    own = EntityMembershipRow.__table__.alias("reached_own")
    share_cap = EntityMembershipCapRow.__table__.alias("reached_share_cap")
    govern = ScopeBindingRow.__table__.alias("reached_govern")
    entity = VirtualEntityRow.__table__.alias("reached_entity")
    governor = VirtualEntityRow.__table__.alias("reached_governor")
    perm = PermissionRow.__table__.alias("reached_permission")
    roles = RoleRow.__table__.alias("reached_role")
    user_roles = UserRoleRow.__table__.alias("reached_user_role")

    bits = int(permission)
    granted = perm.c.permission.op("&")(
        sa.func.coalesce(govern.c.permission_cap, int(Permission.full()))
    )
    return sa.exists(
        sa.select(sa.literal(1))
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
                    perm.c.entity_type == entity_type,
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
            entity.c.entity_id == entity_id,
            user_roles.c.user_id == user_id,
            roles.c.status == RoleStatus.ACTIVE,
            granted.op("&")(bits) == bits,
            # Own answers through every governor. A share answers with a cap row on
            # every field for the bit, and only through the ve's own govern.
            sa.or_(
                own.c.capped.is_(False),
                sa.and_(
                    share_cap.c.id.is_not(None),
                    govern.c.scope_entity_id == govern.c.virtual_entity_id,
                ),
            ),
        )
    )
