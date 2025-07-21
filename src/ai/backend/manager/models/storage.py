from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Mapping,
    Optional,
    Sequence,
    cast,
    override,
)

import aiohttp
import graphene
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import joinedload, load_only, selectinload

from ai.backend.common.types import (
    HardwareMetadata,
    VFolderHostPermission,
    VFolderHostPermissionMap,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import (
    AUTH_TOKEN_HDR,
    StorageProxyInfo,
    StorageSessionManager,
    VolumeInfo,
)  # For compatibility with existing code

from .base import Item, PaginatedList
from .rbac import (
    AbstractPermissionContext,
    AbstractPermissionContextBuilder,
    DomainScope,
    ProjectScope,
    ScopeType,
    UserScope,
    get_predefined_roles_in_scope,
)
from .rbac.context import ClientContext
from .rbac.permission_defs import StorageHostPermission
from .resource_policy import KeyPairResourcePolicyRow
from .user import UserRow

if TYPE_CHECKING:
    from .gql import GraphQueryContext

# Left this for compatibility with existing code
__all__ = (
    "StorageProxyInfo",
    "VolumeInfo",
    "StorageSessionManager",
    "StorageVolume",
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class StorageVolume(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    # id: {proxy_name}:{name}
    backend = graphene.String()
    fsprefix = graphene.String()
    path = graphene.String()
    capabilities = graphene.List(graphene.String)
    hardware_metadata = graphene.JSONString()
    performance_metric = graphene.JSONString()
    usage = graphene.JSONString()
    proxy = graphene.String(
        description="Added in 24.03.0. Name of the proxy which this volume belongs to."
    )
    name = graphene.String(description="Added in 24.03.0. Name of the storage.")

    async def resolve_hardware_metadata(self, info: graphene.ResolveInfo) -> HardwareMetadata:
        ctx: GraphQueryContext = info.context
        return await ctx.registry.gather_storage_hwinfo(self.id)

    async def resolve_performance_metric(self, info: graphene.ResolveInfo) -> Mapping[str, Any]:
        ctx: GraphQueryContext = info.context
        try:
            proxy_name, volume_name = ctx.storage_manager.get_proxy_and_volume(self.id)
            manager_client = ctx.storage_manager.get_manager_facing_client(proxy_name)
            storage_reply = await manager_client.get_volume_performance_metric(volume_name)
            return storage_reply["metric"]
        except aiohttp.ClientResponseError:
            return {}

    async def resolve_usage(self, info: graphene.ResolveInfo) -> Mapping[str, Any]:
        ctx: GraphQueryContext = info.context
        proxy_name, volume_name = ctx.storage_manager.get_proxy_and_volume(self.id)
        try:
            manager_client = ctx.storage_manager.get_manager_facing_client(proxy_name)
            return await manager_client.get_fs_usage(volume_name)
        except aiohttp.ClientResponseError:
            return {}

    @classmethod
    def from_info(cls, proxy_name: str, volume_info: VolumeInfo) -> StorageVolume:
        return cls(
            id=f"{proxy_name}:{volume_info['name']}",
            backend=volume_info["backend"],
            path=volume_info["path"],
            fsprefix=volume_info["fsprefix"],
            capabilities=volume_info["capabilities"],
            name=volume_info["name"],
            proxy=proxy_name,
        )

    @classmethod
    async def load_count(
        cls,
        ctx: GraphQueryContext,
        filter: Optional[str] = None,
    ) -> int:
        volumes = [*await ctx.storage_manager.get_all_volumes()]
        return len(volumes)

    @classmethod
    async def load_slice(
        cls,
        ctx: GraphQueryContext,
        limit: int,
        offset: int,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> Sequence[StorageVolume]:
        # For consistency we add filter/order params here, but it's actually noop.
        if filter is not None or order is not None:
            log.warning(
                "Paginated list of storage volumes igonores custom filtering and/or ordering"
            )
        volumes = [*await ctx.storage_manager.get_all_volumes()]
        return [
            cls.from_info(proxy_name, volume_info)
            for proxy_name, volume_info in volumes[offset : offset + limit]
        ]

    @classmethod
    async def load_by_id(
        cls,
        ctx: GraphQueryContext,
        id: str,
    ) -> StorageVolume:
        proxy_name, volume_name = ctx.storage_manager.get_proxy_and_volume(id)
        try:
            proxy_info = ctx.storage_manager._proxies[proxy_name]
        except KeyError:
            raise ValueError(f"no such storage proxy: {proxy_name!r}")
        async with proxy_info.session.request(
            "GET",
            proxy_info.manager_api_url / "volumes",
            raise_for_status=True,
            headers={AUTH_TOKEN_HDR: proxy_info.secret},
        ) as resp:
            reply = await resp.json()
            for volume_data in reply["volumes"]:
                if volume_data["name"] == volume_name:
                    return cls.from_info(proxy_name, volume_data)
            else:
                raise ValueError(
                    f"no such volume in the storage proxy {proxy_name!r}: {volume_name!r}",
                )


class StorageVolumeList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(StorageVolume, required=True)


# RBAC

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

    @override
    async def calculate_permission(
        self,
        ctx: ClientContext,
        target_scope: ScopeType,
    ) -> frozenset[StorageHostPermission]:
        roles = await get_predefined_roles_in_scope(ctx, target_scope, self.db_session)
        permissions = await self._calculate_permission_by_predefined_roles(roles)
        return permissions

    @override
    async def build_ctx_in_system_scope(
        self,
        ctx: ClientContext,
    ) -> PermissionContext:
        from .domain import DomainRow

        perm_ctx = PermissionContext()
        _domain_query_stmt = sa.select(DomainRow).options(load_only(DomainRow.name))
        for row in await self.db_session.scalars(_domain_query_stmt):
            to_be_merged = await self.build_ctx_in_domain_scope(ctx, DomainScope(row.name))
            perm_ctx.merge(to_be_merged)
        return perm_ctx

    @override
    async def build_ctx_in_domain_scope(
        self,
        ctx: ClientContext,
        scope: DomainScope,
    ) -> PermissionContext:
        from .domain import DomainRow

        permissions = await self.calculate_permission(ctx, scope)
        if not permissions:
            # User is not part of the domain.
            return PermissionContext()

        stmt = (
            sa.select(DomainRow)
            .where(DomainRow.name == scope.domain_name)
            .options(load_only(DomainRow.allowed_vfolder_hosts))
        )
        domain_row = cast(DomainRow | None, await self.db_session.scalar(stmt))
        if domain_row is None:
            return PermissionContext()
        host_permissions = cast(VFolderHostPermissionMap, domain_row.allowed_vfolder_hosts)
        result = PermissionContext(
            object_id_to_additional_permission_map={
                host: _legacy_vf_perms_to_host_rbac_perms(perms)
                for host, perms in host_permissions.items()
            }
        )
        return result

    @override
    async def build_ctx_in_project_scope(
        self,
        ctx: ClientContext,
        scope: ProjectScope,
    ) -> PermissionContext:
        from .group import GroupRow

        permissions = await self.calculate_permission(ctx, scope)
        if not permissions:
            # User is not part of the domain.
            return PermissionContext()

        stmt = (
            sa.select(GroupRow)
            .where(GroupRow.id == scope.project_id)
            .options(load_only(GroupRow.allowed_vfolder_hosts))
        )
        project_row = cast(GroupRow | None, await self.db_session.scalar(stmt))
        if project_row is None:
            return PermissionContext()
        host_permissions = cast(VFolderHostPermissionMap, project_row.allowed_vfolder_hosts)
        result = PermissionContext(
            object_id_to_additional_permission_map={
                host: _legacy_vf_perms_to_host_rbac_perms(perms)
                for host, perms in host_permissions.items()
            }
        )
        return result

    @override
    async def build_ctx_in_user_scope(
        self,
        ctx: ClientContext,
        scope: UserScope,
    ) -> PermissionContext:
        from .keypair import KeyPairRow

        permissions = await self.calculate_permission(ctx, scope)
        if not permissions:
            # User is not part of the domain.
            return PermissionContext()
        stmt = (
            sa.select(UserRow)
            .where(UserRow.uuid == scope.user_id)
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

    @override
    @classmethod
    async def _permission_for_owner(
        cls,
    ) -> frozenset[StorageHostPermission]:
        return OWNER_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_admin(
        cls,
    ) -> frozenset[StorageHostPermission]:
        return ADMIN_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_monitor(
        cls,
    ) -> frozenset[StorageHostPermission]:
        return MONITOR_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_privileged_member(
        cls,
    ) -> frozenset[StorageHostPermission]:
        return PRIVILEGED_MEMBER_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_member(
        cls,
    ) -> frozenset[StorageHostPermission]:
        return MEMBER_PERMISSIONS
