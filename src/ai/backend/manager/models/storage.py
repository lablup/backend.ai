from __future__ import annotations

import asyncio
import enum
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
from sqlalchemy.orm import joinedload, selectinload

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    HardwareMetadata,
    VFolderHostPermission,
    VFolderHostPermissionMap,
    VFolderID,
)

from ..api.exceptions import InvalidAPIParameters, VFolderOperationFailed
from ..exceptions import InvalidArgument
from .acl import (
    AbstractACLPermissionContext,
    AbstractACLPermissionContextBuilder,
    BaseACLPermission,
    BaseACLScope,
    ClientContext,
    DomainScope,
    ProjectScope,
    UserScope,
)
from .base import Item, PaginatedList
from .domain import DomainRow
from .group import GroupRow
from .keypair import KeyPairRow
from .resource_policy import KeyPairResourcePolicyRow
from .user import UserRole, UserRow

if TYPE_CHECKING:
    from .gql import GraphQueryContext

__all__ = (
    "StorageProxyInfo",
    "VolumeInfo",
    "StorageSessionManager",
    "StorageVolume",
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class StorageProxyInfo:
    session: aiohttp.ClientSession
    secret: str
    client_api_url: yarl.URL
    manager_api_url: yarl.URL
    sftp_scaling_groups: list[str]


AUTH_TOKEN_HDR: Final = "X-BackendAI-Storage-Auth-Token"

_ctx_volumes_cache: ContextVar[List[Tuple[str, VolumeInfo]]] = ContextVar("_ctx_volumes")


class StorageHostACLPermission(BaseACLPermission):
    from .vfolder import VFolderACLPermission

    CREATE_FOLDER = enum.auto()

    CLONE = VFolderACLPermission.CLONE
    OVERRIDE_PERMISSION_TO_OTHERS = VFolderACLPermission.OVERRIDE_PERMISSION_TO_OTHERS

    READ_ATTRIBUTE = VFolderACLPermission.READ_ATTRIBUTE
    UPDATE_ATTRIBUTE = VFolderACLPermission.UPDATE_ATTRIBUTE
    DELETE_VFOLDER = VFolderACLPermission.DELETE_VFOLDER

    READ_CONTENT = VFolderACLPermission.READ_CONTENT
    WRITE_CONTENT = VFolderACLPermission.WRITE_CONTENT
    DELETE_CONTENT = VFolderACLPermission.DELETE_CONTENT

    MOUNT_RO = VFolderACLPermission.MOUNT_RO
    MOUNT_RW = VFolderACLPermission.MOUNT_RW
    MOUNT_WD = VFolderACLPermission.MOUNT_WD


ALL_STORAGE_HOST_PERMISSIONS = frozenset([perm for perm in StorageHostACLPermission])


LEGACY_VFHOST_PERMISSION_TO_HOST_ACL_PERMISSION_MAP: Mapping[
    VFolderHostPermission, frozenset[StorageHostACLPermission]
] = {
    VFolderHostPermission.CREATE: frozenset([StorageHostACLPermission.CREATE_FOLDER]),
    VFolderHostPermission.MODIFY: frozenset([StorageHostACLPermission.UPDATE_ATTRIBUTE]),
    VFolderHostPermission.DELETE: frozenset([
        StorageHostACLPermission.DELETE_VFOLDER,
        StorageHostACLPermission.DELETE_CONTENT,
    ]),
    VFolderHostPermission.MOUNT_IN_SESSION: frozenset([
        StorageHostACLPermission.MOUNT_RO,
        StorageHostACLPermission.MOUNT_RW,
        StorageHostACLPermission.MOUNT_WD,
    ]),
    VFolderHostPermission.UPLOAD_FILE: frozenset([
        StorageHostACLPermission.READ_ATTRIBUTE,
        StorageHostACLPermission.WRITE_CONTENT,
        StorageHostACLPermission.DELETE_CONTENT,
    ]),
    VFolderHostPermission.DOWNLOAD_FILE: frozenset([
        StorageHostACLPermission.READ_ATTRIBUTE,
        StorageHostACLPermission.WRITE_CONTENT,
        StorageHostACLPermission.DELETE_CONTENT,
    ]),
    VFolderHostPermission.INVITE_OTHERS: frozenset([
        StorageHostACLPermission.OVERRIDE_PERMISSION_TO_OTHERS
    ]),
    VFolderHostPermission.SET_USER_PERM: frozenset([
        StorageHostACLPermission.OVERRIDE_PERMISSION_TO_OTHERS
    ]),
}

ALL_LEGACY_VFHOST_PERMISSIONS = {perm for perm in VFolderHostPermission}


def _legacy_vf_perms_to_host_acl_perms(
    perms: list[VFolderHostPermission],
) -> frozenset[StorageHostACLPermission]:
    if set(perms) == ALL_LEGACY_VFHOST_PERMISSIONS:
        return ALL_STORAGE_HOST_PERMISSIONS
    result: frozenset[StorageHostACLPermission] = frozenset()
    for perm in perms:
        result |= LEGACY_VFHOST_PERMISSION_TO_HOST_ACL_PERMISSION_MAP[perm]
    return result


@dataclass
class ACLPermissionContext(AbstractACLPermissionContext[StorageHostACLPermission, str, str]):
    @property
    def host_to_permissions_map(self) -> Mapping[str, frozenset[StorageHostACLPermission]]:
        return self.object_id_to_additional_permission_map

    async def build_query(self) -> sa.sql.Select | None:
        return None

    async def determine_permission(self, acl_obj: str) -> frozenset[StorageHostACLPermission]:
        host_name = acl_obj
        return self.object_id_to_additional_permission_map.get(host_name, frozenset())


class ACLPermissionContextBuilder(
    AbstractACLPermissionContextBuilder[StorageHostACLPermission, ACLPermissionContext]
):
    @classmethod
    async def _build_in_user_scope(
        cls,
        db_session: SASession,
        ctx: ClientContext,
        user_id: uuid.UUID,
    ) -> ACLPermissionContext:
        match ctx.user_role:
            case UserRole.SUPERADMIN | UserRole.MONITOR:
                stmt = (
                    sa.select(UserRow)
                    .where(UserRow.uuid == user_id)
                    .options(
                        selectinload(UserRow.keypairs).options(
                            joinedload(KeyPairRow.resource_policy)
                        )
                    )
                )
                user_row = cast(UserRow | None, await db_session.scalar(stmt))
                if user_row is None:
                    return ACLPermissionContext()
            case UserRole.ADMIN:
                stmt = (
                    sa.select(UserRow)
                    .where(UserRow.uuid == user_id)
                    .options(
                        selectinload(UserRow.keypairs).options(
                            joinedload(KeyPairRow.resource_policy)
                        )
                    )
                )
                user_row = cast(UserRow | None, await db_session.scalar(stmt))
                if user_row is None:
                    return ACLPermissionContext()
                if ctx.domain_name != user_row.domain_name:
                    return ACLPermissionContext()
            case UserRole.USER:
                if ctx.user_id != user_id:
                    return ACLPermissionContext()
                stmt = (
                    sa.select(UserRow)
                    .where(UserRow.uuid == user_id)
                    .options(
                        selectinload(UserRow.keypairs).options(
                            joinedload(KeyPairRow.resource_policy)
                        ),
                        joinedload(UserRow.domain),
                    )
                )
                user_row = cast(UserRow | None, await db_session.scalar(stmt))
                if user_row is None:
                    return ACLPermissionContext()

        object_id_to_additional_permission_map: defaultdict[
            str, frozenset[StorageHostACLPermission]
        ] = defaultdict(frozenset)

        for keypair in user_row.keypairs:
            resource_policy = cast(KeyPairResourcePolicyRow | None, keypair.resource_policy)
            if resource_policy is None:
                continue
            host_permissions = cast(VFolderHostPermissionMap, resource_policy.allowed_vfolder_hosts)
            for host, perms in host_permissions.items():
                object_id_to_additional_permission_map[host] |= _legacy_vf_perms_to_host_acl_perms(
                    perms
                )

        return ACLPermissionContext(
            object_id_to_additional_permission_map=object_id_to_additional_permission_map
        )

    @classmethod
    async def _build_in_project_scope(
        cls,
        db_session: SASession,
        ctx: ClientContext,
        project_id: uuid.UUID,
    ) -> ACLPermissionContext:
        role_in_project = await ctx.get_user_role_in_project(project_id)
        if role_in_project is None:
            return ACLPermissionContext()
        stmt = sa.select(GroupRow).where(GroupRow.id == project_id)
        project_row = cast(GroupRow, await db_session.scalar(stmt))
        host_permissions = cast(VFolderHostPermissionMap, project_row.allowed_vfolder_hosts)

        object_id_to_additional_permission_map: defaultdict[
            str, frozenset[StorageHostACLPermission]
        ] = defaultdict(frozenset)
        for host, perms in host_permissions.items():
            object_id_to_additional_permission_map[host] |= _legacy_vf_perms_to_host_acl_perms(
                perms
            )

        return ACLPermissionContext(
            object_id_to_additional_permission_map=object_id_to_additional_permission_map
        )

    @classmethod
    async def _build_in_domain_scope(
        cls,
        db_session: SASession,
        ctx: ClientContext,
        domain_name: str,
    ) -> ACLPermissionContext:
        match ctx.user_role:
            case UserRole.SUPERADMIN | UserRole.MONITOR:
                pass
            case UserRole.ADMIN:
                if ctx.domain_name != domain_name:
                    return ACLPermissionContext()
            case UserRole.USER:
                if ctx.domain_name != domain_name:
                    return ACLPermissionContext()

        stmt = sa.select(DomainRow).where(DomainRow.name == domain_name)
        domain_row = cast(DomainRow | None, await db_session.scalar(stmt))
        if domain_row is None:
            return ACLPermissionContext()
        vfolder_host_permission = cast(VFolderHostPermissionMap, domain_row.allowed_vfolder_hosts)
        return ACLPermissionContext(
            object_id_to_additional_permission_map={
                host: _legacy_vf_perms_to_host_acl_perms(perms)
                for host, perms in vfolder_host_permission.items()
            }
        )


class VolumeInfo(TypedDict):
    name: str
    backend: str
    path: str
    fsprefix: str
    capabilities: List[str]


StorageHostPermissionMap = Mapping[str, frozenset[StorageHostACLPermission]]


async def get_storage_hosts(
    ctx: ClientContext,
    target_scope: BaseACLScope,
    requested_permission: StorageHostACLPermission | None = None,
) -> StorageHostPermissionMap:
    async with SASession(ctx.db_conn) as db_session:
        permission_ctx = await ACLPermissionContextBuilder.build(
            db_session, ctx, target_scope, permission=requested_permission
        )
        return {**permission_ctx.host_to_permissions_map}


def merge_host_permissions(
    left: StorageHostPermissionMap, right: StorageHostPermissionMap
) -> StorageHostPermissionMap:
    result: dict[str, frozenset[StorageHostACLPermission]] = {}
    for host_name in {*left.keys(), *right.keys()}:
        result[host_name] = left.get(host_name, frozenset()) | right.get(host_name, frozenset())
    return result


async def get_client_accessible_storage_hosts(
    ctx: ClientContext,
    requested_permission: StorageHostACLPermission | None = None,
) -> StorageHostPermissionMap:
    kp_scoped_host_permissions = await get_storage_hosts(
        ctx, UserScope(ctx.user_id), requested_permission
    )
    domain_scoped_host_permissions = await get_storage_hosts(
        ctx, DomainScope(ctx.domain_name), requested_permission
    )
    host_permissions = merge_host_permissions(
        kp_scoped_host_permissions, domain_scoped_host_permissions
    )
    project_ctx = await ctx.get_or_init_project_ctx_in_domain(ctx.domain_name)
    if project_ctx is not None:
        for project_id in project_ctx.keys():
            project_scoped_host_permissions = await get_storage_hosts(
                ctx, ProjectScope(project_id), requested_permission
            )
            host_permissions = merge_host_permissions(
                host_permissions, project_scoped_host_permissions
            )
    return host_permissions


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
