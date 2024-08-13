from __future__ import annotations

import asyncio
import itertools
import logging
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager as actxmgr
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Final,
    Iterable,
    List,
    Mapping,
    Sequence,
    Tuple,
    TypedDict,
    cast,
)

import aiohttp
import attrs
import graphene
import sqlalchemy as sa
import yarl
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import joinedload, load_only, selectinload

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    HardwareMetadata,
    VFolderHostPermission,
    VFolderHostPermissionMap,
    VFolderID,
)

from ..api.exceptions import InvalidAPIParameters, VFolderOperationFailed
from ..exceptions import InvalidArgument
from .base import Item, PaginatedList
from .rbac import (
    AbstractPermissionContext,
    AbstractPermissionContextBuilder,
    BaseScope,
    DomainScope,
    ProjectScope,
    UserScope,
    get_roles_in_scope,
)
from .rbac.context import ClientContext
from .rbac.exceptions import InvalidScope
from .rbac.permission_defs import StorageHostPermission
from .resource_policy import KeyPairResourcePolicyRow
from .user import UserRow

if TYPE_CHECKING:
    from .gql import GraphQueryContext

__all__ = (
    "StorageProxyInfo",
    "VolumeInfo",
    "StorageSessionManager",
    "StorageVolume",
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class StorageProxyInfo:
    session: aiohttp.ClientSession
    secret: str
    client_api_url: yarl.URL
    manager_api_url: yarl.URL
    sftp_scaling_groups: list[str]


AUTH_TOKEN_HDR: Final = "X-BackendAI-Storage-Auth-Token"

_ctx_volumes_cache: ContextVar[List[Tuple[str, VolumeInfo]]] = ContextVar("_ctx_volumes")


class VolumeInfo(TypedDict):
    name: str
    backend: str
    path: str
    fsprefix: str
    capabilities: List[str]


class StorageSessionManager:
    _proxies: Mapping[str, StorageProxyInfo]
    _exposed_volume_info: List[str]

    def __init__(self, storage_config: Mapping[str, Any]) -> None:
        self.config = storage_config
        self._exposed_volume_info = self.config["exposed_volume_info"]
        self._proxies = {}
        for proxy_name, proxy_config in self.config["proxies"].items():
            connector = aiohttp.TCPConnector(ssl=proxy_config["ssl_verify"])
            session = aiohttp.ClientSession(connector=connector)
            self._proxies[proxy_name] = StorageProxyInfo(
                session=session,
                secret=proxy_config["secret"],
                client_api_url=yarl.URL(proxy_config["client_api"]),
                manager_api_url=yarl.URL(proxy_config["manager_api"]),
                sftp_scaling_groups=proxy_config["sftp_scaling_groups"],
            )

    async def aclose(self) -> None:
        close_aws = []
        for proxy_info in self._proxies.values():
            close_aws.append(proxy_info.session.close())
        await asyncio.gather(*close_aws, return_exceptions=True)

    @staticmethod
    def split_host(vfolder_host: str) -> Tuple[str, str]:
        proxy_name, _, volume_name = vfolder_host.partition(":")
        return proxy_name, volume_name

    async def get_all_volumes(self) -> Iterable[Tuple[str, VolumeInfo]]:
        """
        Returns a list of tuple
        [(proxy_name: str, volume_info: VolumeInfo), ...]
        """
        try:
            # per-asyncio-task cache
            return _ctx_volumes_cache.get()
        except LookupError:
            pass
        fetch_aws = []

        async def _fetch(
            proxy_name: str,
            proxy_info: StorageProxyInfo,
        ) -> Iterable[Tuple[str, VolumeInfo]]:
            async with proxy_info.session.request(
                "GET",
                proxy_info.manager_api_url / "volumes",
                raise_for_status=True,
                headers={AUTH_TOKEN_HDR: proxy_info.secret},
            ) as resp:
                reply = await resp.json()
                return ((proxy_name, volume_data) for volume_data in reply["volumes"])

        for proxy_name, proxy_info in self._proxies.items():
            fetch_aws.append(_fetch(proxy_name, proxy_info))
        results = [*itertools.chain(*await asyncio.gather(*fetch_aws))]
        _ctx_volumes_cache.set(results)
        return results

    async def get_sftp_scaling_groups(self, proxy_name: str) -> List[str]:
        if proxy_name not in self._proxies:
            raise IndexError(f"proxy {proxy_name} does not exist")
        return self._proxies[proxy_name].sftp_scaling_groups or []

    async def get_mount_path(
        self,
        vfolder_host: str,
        vfolder_id: VFolderID,
        subpath: PurePosixPath = PurePosixPath("."),
    ) -> str:
        async with self.request(
            vfolder_host,
            "GET",
            "folder/mount",
            json={
                "volume": self.split_host(vfolder_host)[1],
                "vfid": str(vfolder_id),
                "subpath": str(subpath),
            },
        ) as (_, resp):
            reply = await resp.json()
            return reply["path"]

    @actxmgr
    async def request(
        self,
        vfolder_host_or_proxy_name: str,
        method: str,
        request_relpath: str,
        *args,
        **kwargs,
    ) -> AsyncIterator[Tuple[yarl.URL, aiohttp.ClientResponse]]:
        proxy_name, _ = self.split_host(vfolder_host_or_proxy_name)
        try:
            proxy_info = self._proxies[proxy_name]
        except KeyError:
            raise InvalidArgument("There is no such storage proxy", proxy_name)
        headers = kwargs.pop("headers", {})
        headers[AUTH_TOKEN_HDR] = proxy_info.secret
        async with proxy_info.session.request(
            method,
            proxy_info.manager_api_url / request_relpath,
            *args,
            headers=headers,
            **kwargs,
        ) as client_resp:
            if client_resp.status // 100 != 2:
                try:
                    error_data = await client_resp.json()
                    raise VFolderOperationFailed(
                        extra_msg=error_data.pop("msg", None),
                        extra_data=error_data,
                    )
                except aiohttp.ClientResponseError:
                    # when the response body is not JSON, just raise with status info.
                    raise VFolderOperationFailed(
                        extra_msg=(
                            "Storage proxy responded with "
                            f"{client_resp.status} {client_resp.reason}"
                        ),
                        extra_data=None,
                    )
                except VFolderOperationFailed as e:
                    if client_resp.status // 100 == 5:
                        raise InvalidAPIParameters(e.extra_msg, e.extra_data)
                    # Raise as-is for semantic failures, not server errors.
                    raise
            yield proxy_info.client_api_url, client_resp


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
        proxy_name, volume_name = ctx.storage_manager.split_host(self.id)
        try:
            proxy_info = ctx.storage_manager._proxies[proxy_name]
        except KeyError:
            raise ValueError(f"no such storage proxy: {proxy_name!r}")
        try:
            async with proxy_info.session.request(
                "GET",
                proxy_info.manager_api_url / "volume/performance-metric",
                json={"volume": volume_name},
                raise_for_status=True,
                headers={AUTH_TOKEN_HDR: proxy_info.secret},
            ) as resp:
                reply = await resp.json()
                return reply["metric"]
        except aiohttp.ClientResponseError:
            return {}

    async def resolve_usage(self, info: graphene.ResolveInfo) -> Mapping[str, Any]:
        ctx: GraphQueryContext = info.context
        proxy_name, volume_name = ctx.storage_manager.split_host(self.id)
        try:
            proxy_info = ctx.storage_manager._proxies[proxy_name]
        except KeyError:
            raise ValueError(f"no such storage proxy: {proxy_name!r}")
        try:
            async with proxy_info.session.request(
                "GET",
                proxy_info.manager_api_url / "folder/fs-usage",
                json={"volume": volume_name},
                raise_for_status=True,
                headers={AUTH_TOKEN_HDR: proxy_info.secret},
            ) as resp:
                reply = await resp.json()
                return reply
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
        filter: str = None,
    ) -> int:
        volumes = [*await ctx.storage_manager.get_all_volumes()]
        return len(volumes)

    @classmethod
    async def load_slice(
        cls,
        ctx: GraphQueryContext,
        limit: int,
        offset: int,
        filter: str = None,
        order: str = None,
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
        proxy_name, volume_name = ctx.storage_manager.split_host(id)
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
        from .domain import DomainRow

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
        from .group import GroupRow

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
                host: _legacy_vf_perms_to_host_rbac_perms(perms)
                for host, perms in host_permissions.items()
            }
        )
        return result

    async def build_in_user_scope(
        self,
        ctx: ClientContext,
        user_id: uuid.UUID,
    ) -> PermissionContext:
        from .keypair import KeyPairRow

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
