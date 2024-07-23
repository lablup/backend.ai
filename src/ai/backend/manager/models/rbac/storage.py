import uuid
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import joinedload, load_only, selectinload

from ai.backend.common.types import VFolderHostPermission, VFolderHostPermissionMap

from ..domain import DomainRow
from ..group import GroupRow
from ..keypair import KeyPairRow
from ..resource_policy import KeyPairResourcePolicyRow
from ..user import UserRow
from . import (
    AbstractPermissionContext,
    AbstractPermissionContextBuilder,
    BaseScope,
    DomainScope,
    ProjectScope,
    UserScope,
    get_roles_in_scope,
)
from .context import ClientContext
from .exceptions import InvalidScope
from .permission_defs import StorageHostPermission

ALL_STORAGE_HOST_PERMISSIONS: frozenset[StorageHostPermission] = frozenset([
    perm for perm in StorageHostPermission
])
OWNER_PERMISSIONS: frozenset[StorageHostPermission] = ALL_STORAGE_HOST_PERMISSIONS
ADMIN_PERMISSIONS: frozenset[StorageHostPermission] = ALL_STORAGE_HOST_PERMISSIONS
MONITOR_PERMISSIONS: frozenset[StorageHostPermission] = ALL_STORAGE_HOST_PERMISSIONS
PRIVILEGED_MEMBER_PERMISSIONS: frozenset[StorageHostPermission] = ALL_STORAGE_HOST_PERMISSIONS
MEMBER_PERMISSIONS: frozenset[StorageHostPermission] = ALL_STORAGE_HOST_PERMISSIONS

LEGACY_VFHOST_PERMISSION_TO_HOST__PERMISSION_MAP: Mapping[
    VFolderHostPermission, frozenset[StorageHostPermission]
] = {
    VFolderHostPermission.CREATE: frozenset([StorageHostPermission.CREATE_FOLDER]),
    VFolderHostPermission.MODIFY: frozenset([StorageHostPermission.UPDATE_ATTRIBUTE]),
    VFolderHostPermission.DELETE: frozenset([
        StorageHostPermission.DELETE_VFOLDER,
        StorageHostPermission.DELETE_CONTENT,
    ]),
    VFolderHostPermission.MOUNT_IN_SESSION: frozenset([
        StorageHostPermission.MOUNT_RO,
        StorageHostPermission.MOUNT_RW,
        StorageHostPermission.MOUNT_WD,
    ]),
    VFolderHostPermission.UPLOAD_FILE: frozenset([
        StorageHostPermission.READ_ATTRIBUTE,
        StorageHostPermission.WRITE_CONTENT,
        StorageHostPermission.DELETE_CONTENT,
    ]),
    VFolderHostPermission.DOWNLOAD_FILE: frozenset([
        StorageHostPermission.READ_ATTRIBUTE,
        StorageHostPermission.WRITE_CONTENT,
        StorageHostPermission.DELETE_CONTENT,
    ]),
    VFolderHostPermission.INVITE_OTHERS: frozenset([
        StorageHostPermission.ASSIGN_PERMISSION_TO_OTHERS
    ]),
    VFolderHostPermission.SET_USER_PERM: frozenset([
        StorageHostPermission.ASSIGN_PERMISSION_TO_OTHERS
    ]),
}

ALL_LEGACY_VFHOST_PERMISSIONS = {perm for perm in VFolderHostPermission}


def _legacy_vf_perms_to_host_rbac_perms(
    perms: list[VFolderHostPermission],
) -> frozenset[StorageHostPermission]:
    if set(perms) == ALL_LEGACY_VFHOST_PERMISSIONS:
        return ALL_STORAGE_HOST_PERMISSIONS
    result: frozenset[StorageHostPermission] = frozenset()
    for perm in perms:
        result |= LEGACY_VFHOST_PERMISSION_TO_HOST__PERMISSION_MAP[perm]
    return result


StorageHostToPermissionMap = Mapping[str, frozenset[StorageHostPermission]]


@dataclass
class PermissionContext(AbstractPermissionContext[StorageHostPermission, str, str]):
    @property
    def host_to_permissions_map(self) -> StorageHostToPermissionMap:
        return self.object_id_to_additional_permission_map

    async def build_query(self) -> sa.sql.Select | None:
        return None

    async def calculate_final_permission(self, rbac_obj: str) -> frozenset[StorageHostPermission]:
        host_name = rbac_obj
        return self.object_id_to_additional_permission_map.get(host_name, frozenset())


class PermissionContextBuilder(
    AbstractPermissionContextBuilder[StorageHostPermission, PermissionContext]
):
    db_session: SASession

    def __init__(self, db_session: SASession) -> None:
        self.db_session = db_session

    async def build(
        self,
        ctx: ClientContext,
        target_scope: BaseScope,
        requested_permission: StorageHostPermission,
    ) -> PermissionContext:
        match target_scope:
            case DomainScope(domain_name):
                permission_ctx = await self.build_in_domain_scope(ctx, domain_name)
            case ProjectScope(project_id, _):
                permission_ctx = await self.build_in_project_scope(ctx, project_id)
            case UserScope(user_id, _):
                permission_ctx = await self.build_in_user_scope(ctx, user_id)
            case _:
                raise InvalidScope
        permission_ctx.filter_by_permission(requested_permission)
        return permission_ctx

    async def build_in_domain_scope(
        self,
        ctx: ClientContext,
        domain_name: str,
    ) -> PermissionContext:
        roles = await get_roles_in_scope(ctx, DomainScope(domain_name), self.db_session)
        if not roles:
            # User is not part of the domain.
            return PermissionContext()

        stmt = (
            sa.select(DomainRow)
            .where(DomainRow.name == domain_name)
            .options(load_only(DomainRow.allowed_vfolder_hosts))
        )
        domain_row = cast(DomainRow | None, await self.db_session.scalar(stmt))
        if domain_row is None:
            return PermissionContext()
        host_permissions = cast(VFolderHostPermissionMap, domain_row.allowed_vfolder_hosts)
        result = PermissionContext(
            object_id_to_additional_permission_map={
                host: _legacy_vf_perms_to_host_rbac_perms(perms) for host, perms in host_permissions
            }
        )
        return result

    async def build_in_project_scope(
        self,
        ctx: ClientContext,
        project_id: uuid.UUID,
    ) -> PermissionContext:
        roles = await get_roles_in_scope(ctx, ProjectScope(project_id), self.db_session)
        if not roles:
            # User is not part of the project.
            return PermissionContext()

        stmt = (
            sa.select(GroupRow)
            .where(GroupRow.id == project_id)
            .options(load_only(GroupRow.allowed_vfolder_hosts))
        )
        project_row = cast(GroupRow | None, await self.db_session.scalar(stmt))
        if project_row is None:
            return PermissionContext()
        host_permissions = cast(VFolderHostPermissionMap, project_row.allowed_vfolder_hosts)
        result = PermissionContext(
            object_id_to_additional_permission_map={
                host: _legacy_vf_perms_to_host_rbac_perms(perms) for host, perms in host_permissions
            }
        )
        return result

    async def build_in_user_scope(
        self,
        ctx: ClientContext,
        user_id: uuid.UUID,
    ) -> PermissionContext:
        roles = await get_roles_in_scope(ctx, UserScope(user_id), self.db_session)
        if not roles:
            return PermissionContext()
        stmt = (
            sa.select(UserRow)
            .where(UserRow.uuid == user_id)
            .options(
                selectinload(UserRow.keypairs).options(
                    joinedload(KeyPairRow.resource_policy).options(
                        load_only(KeyPairResourcePolicyRow.allowed_vfolder_hosts)
                    )
                )
            )
        )
        user_row = cast(UserRow | None, await self.db_session.scalar(stmt))
        if user_row is None:
            return PermissionContext()

        object_id_to_additional_permission_map: defaultdict[
            str, frozenset[StorageHostPermission]
        ] = defaultdict(frozenset)

        for keypair in user_row.keypairs:
            resource_policy = cast(KeyPairResourcePolicyRow | None, keypair.resource_policy)
            if resource_policy is None:
                continue
            host_permissions = cast(VFolderHostPermissionMap, resource_policy.allowed_vfolder_hosts)
            for host, perms in host_permissions.items():
                object_id_to_additional_permission_map[host] |= _legacy_vf_perms_to_host_rbac_perms(
                    perms
                )

        result = PermissionContext(
            object_id_to_additional_permission_map=object_id_to_additional_permission_map
        )
        return result

    @classmethod
    async def _permission_for_owner(
        cls,
    ) -> frozenset[StorageHostPermission]:
        return OWNER_PERMISSIONS

    @classmethod
    async def _permission_for_admin(
        cls,
    ) -> frozenset[StorageHostPermission]:
        return ADMIN_PERMISSIONS

    @classmethod
    async def _permission_for_monitor(
        cls,
    ) -> frozenset[StorageHostPermission]:
        return MONITOR_PERMISSIONS

    @classmethod
    async def _permission_for_privileged_member(
        cls,
    ) -> frozenset[StorageHostPermission]:
        return PRIVILEGED_MEMBER_PERMISSIONS

    @classmethod
    async def _permission_for_member(
        cls,
    ) -> frozenset[StorageHostPermission]:
        return MEMBER_PERMISSIONS
