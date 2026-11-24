"""What a vfolder answers with for one user."""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.types import VFolderMountPolicy
from ai.backend.manager.models.base import StrEnumType
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.vfolder.row import VFolderRow, VFolderUserMountPolicyRow
from ai.backend.manager.models.virtual_entity.permission_reach import user_permission_reaches
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow

__all__ = ("mount_permission_of_user",)


def mount_permission_of_user(user_id: UserID) -> sa.ColumnElement[VFolderMountPolicy]:
    """The level the user mounts the vfolder at.

    ``resolve_mount_policy`` applies the same rule to loaded rows; change both together.
    """
    policy_type = StrEnumType(VFolderMountPolicy)
    policy_set_for_user = (
        sa.select(VFolderUserMountPolicyRow.permission)
        .where(
            VFolderUserMountPolicyRow.vfolder_id == VFolderRow.id,
            VFolderUserMountPolicyRow.user_id == user_id,
        )
        .correlate(VFolderRow)
        .scalar_subquery()
    )
    return sa.case(
        (
            sa.not_(_vfolder_readable_by_user(user_id)),
            sa.literal(VFolderMountPolicy.NONE, policy_type),
        ),
        (
            VFolderRow.user == user_id,
            sa.literal(VFolderMountPolicy.READ_WRITE, policy_type),
        ),
        else_=sa.func.coalesce(policy_set_for_user, VFolderRow.default_mount_permission),
    )


def _vfolder_readable_by_user(user_id: UserID) -> sa.ColumnElement[bool]:
    """``user_permission_reaches`` leaves out superadmins, who read every vfolder
    that has a node."""
    is_superadmin = sa.exists(
        sa.select(sa.literal(1))
        .where(UserRow.uuid == user_id, UserRow.role == UserRole.SUPERADMIN)
        .correlate(None)
    )
    has_node = sa.exists(
        sa.select(sa.literal(1))
        .where(
            VirtualEntityRow.entity_type == VFolderEntityType(),
            VirtualEntityRow.entity_id == VFolderRow.id,
        )
        .correlate(VFolderRow)
    )
    return sa.or_(
        user_permission_reaches(user_id, Permission.READ, VFolderEntityType(), VFolderRow.id),
        sa.and_(is_superadmin, has_node),
    )
