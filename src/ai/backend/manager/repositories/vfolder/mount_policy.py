"""The mount level a user gets on a vfolder.

Access and mount level are two axes: the RBAC graph answers whether the user may reach
the folder, and the folder's default with the per-user policy rows answer how it mounts.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.types import VFolderMountPolicy

__all__ = ("MountPolicyInputs", "resolve_mount_policy")


@dataclass(frozen=True)
class MountPolicyInputs:
    """What one folder contributes to a user's mount level: its owner, its default,
    and the user's own row over it when one stands."""

    owner_user_id: uuid.UUID | None
    default_mount_permission: VFolderMountPolicy
    user_policy: VFolderMountPolicy | None


def resolve_mount_policy(
    user_id: uuid.UUID,
    *,
    owner_user_id: uuid.UUID | None,
    default_mount_permission: VFolderMountPolicy,
    held: Permission,
    user_policy: VFolderMountPolicy | None,
) -> VFolderMountPolicy:
    """The level one user mounts one folder at.

    No read access mounts nothing. The owner of a personal folder mounts it read-write
    regardless. Otherwise the user's own row answers, then the folder's default.
    """
    if not held.covers(Permission.READ):
        return VFolderMountPolicy.NONE
    if owner_user_id is not None and owner_user_id == user_id:
        return VFolderMountPolicy.READ_WRITE
    if user_policy is not None:
        return user_policy
    return default_mount_permission
