"""Caller-relative access rules for vfolders.

The v1 REST routes resolved the caller's ownership and mount permission in the
``_vfolder_resolver`` route middleware, which refused a write to a folder the
caller only held ``ro`` on before any handler ran. The v2 routes carry no such
middleware, so the same rules live here and the v2 service methods apply them.
"""

import uuid
from collections.abc import Sequence

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.data.vfolder.types import (
    VFolderAccessInfo,
    VFolderData,
    VFolderMountPermission,
    VFolderOwnershipType,
)
from ai.backend.manager.errors.storage import VFolderPermissionError
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository

_PRIVILEGED_ROLES = (UserRole.ADMIN, UserRole.SUPERADMIN)


def resolve_access_info(
    vfolder_data: VFolderData,
    user_id: uuid.UUID,
    granted_permission: VFolderMountPermission | None,
) -> VFolderAccessInfo:
    """Resolve what ``user_id`` may do with ``vfolder_data``.

    ``granted_permission`` is the mount permission the caller holds through an
    accepted invitation (their ``vfolder_permissions`` row), or ``None`` when
    they hold none. A caller who reaches the folder some other way — an admin
    acting on a user folder they were never invited to — gets an
    ``effective_permission`` of ``None``; whether that is allowed is each
    service method's own rule.
    """
    if vfolder_data.ownership_type == VFolderOwnershipType.USER:
        if vfolder_data.user == user_id:
            # The owner reads their own folder's permission, the same value
            # ``query_accessible_vfolders`` reports for a folder one owns. Their
            # write access does not depend on it — see ``ensure_writable``.
            return VFolderAccessInfo(
                vfolder_data=vfolder_data,
                is_owner=True,
                effective_permission=vfolder_data.permission,
            )
        return VFolderAccessInfo(
            vfolder_data=vfolder_data,
            is_owner=False,
            effective_permission=granted_permission,
        )
    # A project-owned folder belongs to nobody personally. Every member that can
    # reach it inherits the folder's own mount permission, unless an explicit
    # grant overrides it — the same precedence ``query_accessible_vfolders`` uses.
    return VFolderAccessInfo(
        vfolder_data=vfolder_data,
        is_owner=False,
        effective_permission=granted_permission or vfolder_data.permission,
    )


async def load_access_info(
    vfolder_repository: VfolderRepository,
    vfolder_data: VFolderData,
    user_id: uuid.UUID,
) -> VFolderAccessInfo:
    """Resolve a single folder's access info, reading the caller's grant first."""
    granted = await vfolder_repository.get_granted_mount_permissions([vfolder_data.id], user_id)
    return resolve_access_info(vfolder_data, user_id, granted.get(vfolder_data.id))


async def load_access_infos(
    vfolder_repository: VfolderRepository,
    vfolder_data: Sequence[VFolderData],
    user_id: uuid.UUID,
) -> list[VFolderAccessInfo]:
    """Resolve access info for a page of folders with one grant lookup."""
    granted = await vfolder_repository.get_granted_mount_permissions(
        [data.id for data in vfolder_data], user_id
    )
    return [resolve_access_info(data, user_id, granted.get(data.id)) for data in vfolder_data]


def ensure_writable(access_info: VFolderAccessInfo, user_role: UserRole | None) -> None:
    """Refuse a content-modifying operation on a folder the caller may only read.

    An owner always writes to their own folder — ``query_accessible_vfolders``
    never applied the mount-permission filter to folders one owns. Admins keep
    the privileged access the same query gave them.
    """
    if access_info.is_owner or user_role in _PRIVILEGED_ROLES:
        return
    permission = access_info.effective_permission
    if permission is None or not permission.is_writable():
        raise VFolderPermissionError(
            f"VFolder {access_info.vfolder_data.id} is not writable by this user"
        )
