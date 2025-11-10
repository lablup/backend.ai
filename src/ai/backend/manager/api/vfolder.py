from __future__ import annotations

import asyncio
import functools
import logging
import math
import textwrap
import uuid
from enum import StrEnum
from http import HTTPStatus
from pathlib import Path
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Concatenate,
    Dict,
    Mapping,
    MutableMapping,
    ParamSpec,
    Sequence,
    Tuple,
    TypeAlias,
    cast,
)

import aiohttp
import aiohttp_cors
import aiotools
import attrs
import sqlalchemy as sa
import trafaret as t
from aiohttp import web
from pydantic import (
    AliasChoices,
    Field,
    computed_field,
)
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common import msgpack
from ai.backend.common import typed_validators as tv
from ai.backend.common import validators as tx
from ai.backend.common.api_handlers import BaseFieldModel
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import (
    VFolderHostPermission,
    VFolderHostPermissionMap,
    VFolderID,
    VFolderUsageMode,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.resource import get_watcher_info
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.data.permission.types import ScopeType
from ai.backend.manager.models.storage import StorageSessionManager

from ..errors.api import InvalidAPIParameters
from ..errors.auth import InsufficientPrivilege
from ..errors.common import InternalServerError, ObjectNotFound
from ..errors.kernel import BackendAgentError
from ..errors.service import ModelServiceDependencyNotCleared
from ..errors.storage import (
    TooManyVFoldersFound,
    VFolderFilterStatusFailed,
    VFolderFilterStatusNotAvailable,
    VFolderNotFound,
    VFolderOperationFailed,
)
from ..models import (
    ACTIVE_USER_STATUSES,
    EndpointRow,
    UserRole,
    UserStatus,
    VFolderInvitationState,
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
    VFolderPermissionSetAlias,
    VFolderPermissionValidator,
    VFolderStatusSet,
    agents,
    ensure_host_permission_allowed,
    get_allowed_vfolder_hosts_by_group,
    get_allowed_vfolder_hosts_by_user,
    kernels,
    keypair_resource_policies,
    keypairs,
    query_accessible_vfolders,
    update_vfolder_status,
    users,
    vfolder_invitations,
    vfolder_permissions,
    vfolder_status_map,
    vfolders,
)
from ..models.user import UserRow
from ..models.utils import execute_with_retry, execute_with_txn_retry
from ..models.vfolder import (
    VFolderPermissionRow,
    delete_vfolder_relation_rows,
    is_unmanaged,
)
from ..models.vfolder import VFolderRow as VFolderDBRow
from ..services.vfolder.actions.base import (
    CloneVFolderAction,
    CreateVFolderAction,
    DeleteForeverVFolderAction,
    ForceDeleteVFolderAction,
    GetVFolderAction,
    ListVFolderAction,
    MoveToTrashVFolderAction,
    RestoreVFolderFromTrashAction,
    UpdateVFolderAttributeAction,
    VFolderAttributeModifier,
)
from ..services.vfolder.actions.file import (
    CreateDownloadSessionAction,
    CreateUploadSessionAction,
    DeleteFilesAction,
    ListFilesAction,
    MkdirAction,
    RenameFileAction,
)
from ..services.vfolder.actions.invite import (
    AcceptInvitationAction,
    InviteVFolderAction,
    LeaveInvitedVFolderAction,
    ListInvitationAction,
    RejectInvitationAction,
    RevokeInvitedVFolderAction,
    UpdateInvitationAction,
    UpdateInvitedVFolderMountPermissionAction,
)
from ..services.vfolder.exceptions import (
    ModelServiceDependencyNotCleared as VFolderMountedOnModelService,
)
from ..services.vfolder.exceptions import (
    VFolderAlreadyExists,
    VFolderInvalidParameter,
)
from ..types import OptionalState
from .auth import admin_required, auth_required, superadmin_required
from .manager import ALL_ALLOWED, READ_ALLOWED, server_status_required
from .utils import (
    LegacyBaseRequestModel,
    LegacyBaseResponseModel,
    check_api_params,
    get_user_scopes,
    pydantic_params_api_handler,
)

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

VFolderRow: TypeAlias = Mapping[str, Any]
P = ParamSpec("P")


class SuccessResponseModel(LegacyBaseResponseModel):
    success: bool = Field(default=True)


async def check_vfolder_status(
    folder_row: VFolderRow,
    status: VFolderStatusSet,
) -> None:
    """
    Checks if the target vfolder status matches one of the status sets aliased by `status` VFolderStatusSet,
    and when check fails, raises VFolderFilterStatusFailed.
    This function should prevent user from accessing VFolders which are performing critical operations
    (e.g. VFolder cloning, removal, ...).
    This helper can be combined with `resolve_vfolders
    """

    available_vf_statuses = vfolder_status_map.get(status)
    if not available_vf_statuses:
        raise VFolderFilterStatusNotAvailable
    if folder_row["status"] not in available_vf_statuses:
        raise VFolderFilterStatusFailed


def with_vfolder_status_checked(
    status: VFolderStatusSet,
) -> Callable[
    [Callable[Concatenate[web.Request, VFolderRow, P], Awaitable[web.Response]]],
    Callable[Concatenate[web.Request, Sequence[VFolderRow], P], Awaitable[web.Response]],
]:
    """
    Checks if the target vfolder status matches one of the status sets aliased by `status` VFolderStatusSet.
    This function should prevent user from accessing VFolders which are performing critical operations
    (e.g. VFolder being cloned, being removed, ...).
    This helper can be combined with `resolve_vfolders
    """

    def _wrapper(
        handler: Callable[Concatenate[web.Request, VFolderRow, P], Awaitable[web.Response]],
    ) -> Callable[Concatenate[web.Request, Sequence[VFolderRow], P], Awaitable[web.Response]]:
        @functools.wraps(handler)
        async def _wrapped(
            request: web.Request,
            folder_rows: Sequence[VFolderRow],
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> web.Response:
            if len(folder_rows) > 1:
                raise TooManyVFoldersFound(folder_rows)
            if len(folder_rows) == 0:
                raise VFolderNotFound()
            row = folder_rows[0]
            await check_vfolder_status(row, status)
            return await handler(request, row, *args, **kwargs)

        return _wrapped

    return _wrapper


async def resolve_vfolder_rows(
    request: web.Request,
    perm: VFolderPermissionSetAlias | VFolderPermission | str,
    folder_id_or_name: str | uuid.UUID,
    *,
    allowed_status_set: VFolderStatusSet | None = None,
    allow_privileged_access: bool = False,
) -> Sequence[VFolderRow]:
    """
    Checks if the target VFolder exists and is either:
    - owned by requester, or
    - original owner (of target VFolder) has granted certain level of access to the requester

    When requester passes VFolder name to `folder_id_or_name` parameter then there is a possibility for
    this helper to return multiple entries of VFolder rows which are considered deleted,
    since Backend.AI also is aware of both deleted and purged VFolders. Resolving VFolder row by ID
    will not fall in such cases as it is guaranted by DB side that every VFolder ID is unique across whole table.
    To avoid such behavior, either do not consider VFolder name as an index to resolve VFolder row or
    pass every returned elements of this helper to a separate check_vfolder_status() call, so that
    the handler can figure out which row is the actual row that is aware of.
    """

    root_ctx: RootContext = request.app["_root.context"]
    domain_name = request["user"]["domain_name"]
    user_role = request["user"]["role"]
    user_uuid = request["user"]["uuid"]
    allowed_vfolder_types = (
        await root_ctx.config_provider.legacy_etcd_config_loader.get_vfolder_types()
    )
    vf_user_cond = None
    vf_group_cond = None

    match perm:
        case VFolderPermissionSetAlias():
            invited_perm_cond = vfolder_permissions.c.permission.in_(list(perm.value))
            if not request["is_admin"]:
                vf_group_cond = vfolders.c.permission.in_(list(perm.value))
        case _:
            # Otherwise, just compare it as-is (for future compatibility).
            invited_perm_cond = vfolder_permissions.c.permission == perm
            if not request["is_admin"]:
                vf_group_cond = vfolders.c.permission == perm

    match folder_id_or_name:
        case str():
            extra_vf_conds = vfolders.c.name == folder_id_or_name
        case uuid.UUID():
            extra_vf_conds = vfolders.c.id == folder_id_or_name
        case _:
            raise RuntimeError(f"Unsupported VFolder index type {type(folder_id_or_name)}")

    async with root_ctx.db.begin_readonly() as conn:
        entries = await query_accessible_vfolders(
            conn,
            user_uuid,
            allow_privileged_access=allow_privileged_access,
            user_role=user_role,
            domain_name=domain_name,
            allowed_vfolder_types=allowed_vfolder_types,
            extra_vf_conds=extra_vf_conds,
            extra_invited_vf_conds=invited_perm_cond,
            extra_vf_user_conds=vf_user_cond,
            extra_vf_group_conds=vf_group_cond,
            allowed_status_set=allowed_status_set,
        )
        if len(entries) == 0:
            raise VFolderNotFound(extra_data=folder_id_or_name)
        return entries


def with_vfolder_rows_resolved(
    perm: VFolderPermissionSetAlias | VFolderPermission,
    *,
    allow_privileged_access: bool = False,
) -> Callable[
    [Callable[Concatenate[web.Request, Sequence[VFolderRow], P], Awaitable[web.Response]]],
    Callable[Concatenate[web.Request, P], Awaitable[web.Response]],
]:
    """
    Decorator to pass result of `resolve_vfolder_rows()` to request handler. Index of VFolder is
    extracted from `name` path parameter. When multiple VFolder entries share same name, this decorator
    will pass every rows matching with the name and it is up to `with_vfolder_status_checked` decorator
    to filter out only row with its status matching the intention of the handler.
    Check documentation of `resolve_vfolder_rows()` for more information.
    """

    def _wrapper(
        handler: Callable[
            Concatenate[web.Request, Sequence[VFolderRow], P], Awaitable[web.Response]
        ],
    ) -> Callable[Concatenate[web.Request, P], Awaitable[web.Response]]:
        @functools.wraps(handler)
        async def _wrapped(request: web.Request, *args: P.args, **kwargs: P.kwargs) -> web.Response:
            folder_name_or_id: str | uuid.UUID
            piece = request.match_info["name"]
            try:
                folder_name_or_id = uuid.UUID(piece)
            except ValueError:
                folder_name_or_id = piece
            return await handler(
                request,
                await resolve_vfolder_rows(
                    request,
                    perm,
                    folder_name_or_id,
                    allow_privileged_access=allow_privileged_access,
                ),
                *args,
                **kwargs,
            )

        return _wrapped

    return _wrapper


def vfolder_check_exists(
    handler: Callable[Concatenate[web.Request, VFolderRow, P], Awaitable[web.Response]],
) -> Callable[Concatenate[web.Request, P], Awaitable[web.Response]]:
    """
    Checks if the target vfolder exists and is owned by the current user.

    The decorated handler should accept an extra "row" argument
    which contains the matched VirtualFolder table row.
    """

    @functools.wraps(handler)
    async def _wrapped(request: web.Request, *args: P.args, **kwargs: P.kwargs) -> web.Response:
        root_ctx: RootContext = request.app["_root.context"]
        user_uuid = request["user"]["uuid"]
        folder_name = request.match_info["name"]
        async with root_ctx.db.begin() as conn:
            j = sa.join(
                vfolders,
                vfolder_permissions,
                vfolders.c.id == vfolder_permissions.c.vfolder,
                isouter=True,
            )
            query = (
                sa.select("*")
                .select_from(j)
                .where(
                    ((vfolders.c.user == user_uuid) | (vfolder_permissions.c.user == user_uuid))
                    & (vfolders.c.name == folder_name)
                )
            )
            try:
                result = await conn.execute(query)
            except sa.exc.DataError:
                raise InvalidAPIParameters
            row = result.first()
            if row is None:
                raise VFolderNotFound()
        return await handler(request, row, *args, **kwargs)

    return _wrapped


class CreateRequestModel(LegacyBaseRequestModel):
    name: tv.VFolderName = Field(description="Name of the vfolder")
    folder_host: str | None = Field(default=None, alias="host")
    usage_mode: VFolderUsageMode = Field(default=VFolderUsageMode.GENERAL)
    permission: VFolderPermission = Field(default=VFolderPermission.READ_WRITE)
    unmanaged_path: str | None = Field(default=None, alias="unmanagedPath")
    group_id_or_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("group", "groupId"),
    )
    cloneable: bool = Field(default=False)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def parsed_group_id_or_name(self) -> str | uuid.UUID | None:
        group_id_or_name: str | uuid.UUID | None
        match self.group_id_or_name:
            case str():
                try:
                    group_id_or_name = uuid.UUID(self.group_id_or_name)
                except ValueError:
                    group_id_or_name = self.group_id_or_name
            case _:
                group_id_or_name = self.group_id_or_name
        return group_id_or_name


@auth_required
@server_status_required(ALL_ALLOWED)
@pydantic_params_api_handler(CreateRequestModel)
async def create(request: web.Request, params: CreateRequestModel) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    user_role = request["user"]["role"]
    user_uuid: uuid.UUID = request["user"]["uuid"]
    keypair_resource_policy = request["keypair"]["resource_policy"]
    domain_name = request["user"]["domain_name"]
    group_id_or_name = params.parsed_group_id_or_name
    log.info(
        "VFOLDER.CREATE (email:{}, ak:{}, vf:{}, vfh:{}, umod:{}, perm:{})",
        request["user"]["email"],
        access_key,
        params.name,
        params.folder_host,
        params.usage_mode.value,
        params.permission.value,
    )
    folder_host = params.folder_host
    unmanaged_path = params.unmanaged_path

    if group_id_or_name is not None:
        scope_type = ScopeType.PROJECT
        scope_id = str(group_id_or_name)
    else:
        scope_type = ScopeType.USER
        scope_id = str(user_uuid)

    try:
        result = await root_ctx.processors.vfolder.create_vfolder.wait_for_complete(
            CreateVFolderAction(
                name=params.name,
                keypair_resource_policy=keypair_resource_policy,
                domain_name=domain_name,
                group_id_or_name=group_id_or_name,
                folder_host=folder_host,
                unmanaged_path=unmanaged_path,
                mount_permission=params.permission,
                usage_mode=params.usage_mode,
                cloneable=params.cloneable,
                user_uuid=user_uuid,
                user_role=user_role,
                creator_email=request["user"]["email"],
                _scope_type=scope_type,
                _scope_id=scope_id,
            )
        )
    except (VFolderInvalidParameter, VFolderAlreadyExists) as e:
        raise InvalidAPIParameters(str(e))
    except BackendAIError as e:
        raise InternalServerError(str(e))
    resp = {
        "id": result.id.hex,
        "name": result.name,
        "quota_scope_id": str(result.quota_scope_id),
        "host": result.host,
        "usage_mode": result.usage_mode.value,
        "permission": result.mount_permission.value,
        "max_size": 0,  # migrated to quota scopes, no longer valid
        "creator": result.creator_email,
        "ownership_type": result.ownership_type.value,
        "user": str(result.user_uuid)
        if result.ownership_type == VFolderOwnershipType.USER
        else None,
        "group": str(result.group_uuid)
        if result.ownership_type == VFolderOwnershipType.GROUP
        else None,
        "cloneable": result.cloneable,
        "status": result.status,
    }
    if unmanaged_path:
        resp["unmanaged_path"] = unmanaged_path
    return web.json_response(resp, status=HTTPStatus.CREATED)


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key("all", default=False): t.ToBool,
        tx.AliasedKey(["group_id", "groupId"], default=None): tx.UUID | t.String | t.Null,
        tx.AliasedKey(["owner_user_email", "ownerUserEmail"], default=None): t.Email | t.Null,
    }),
)
async def list_folders(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    log.info(
        "VFOLDER.LIST (email:{}, ak:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
    )
    owner_user_uuid, owner_user_role = await get_user_scopes(request, params)
    group_id = params["group_id"]
    if group_id is not None:
        scope_type = ScopeType.PROJECT
        scope_id = str(group_id)
    else:
        scope_type = ScopeType.USER
        scope_id = str(owner_user_uuid)
    result = await root_ctx.processors.vfolder.list_vfolder.wait_for_complete(
        ListVFolderAction(
            user_uuid=owner_user_uuid,
            _scope_type=scope_type,
            _scope_id=scope_id,
        )
    )
    resp = []
    for base_info, ownership_info in result.vfolders:
        resp.append({
            "name": base_info.name,
            "id": base_info.id.hex,
            "quota_scope_id": str(base_info.quota_scope_id),
            "host": base_info.host,
            "status": base_info.status,
            "usage_mode": base_info.usage_mode.value,
            "created_at": str(base_info.created_at),
            "is_owner": ownership_info.is_owner,
            "permission": base_info.mount_permission.value,
            "user": str(ownership_info.user_uuid) if ownership_info.user_uuid else None,
            "group": str(ownership_info.group_uuid) if ownership_info.group_uuid else None,
            "creator": ownership_info.creator_email,
            "ownership_type": ownership_info.ownership_type.value,
            "cloneable": base_info.cloneable,
        })
    return web.json_response(resp, status=HTTPStatus.OK)


class ExposedVolumeInfoField(StrEnum):
    percentage = "percentage"
    used_bytes = "used_bytes"
    capacity_bytes = "capacity_bytes"


async def fetch_exposed_volume_fields(
    storage_manager: StorageSessionManager,
    valkey_stat_client: ValkeyStatClient,
    proxy_name: str,
    volume_name: str,
) -> Dict[str, int | float]:
    volume_usage = {}

    show_percentage = ExposedVolumeInfoField.percentage in storage_manager._exposed_volume_info
    show_used = ExposedVolumeInfoField.used_bytes in storage_manager._exposed_volume_info
    show_total = ExposedVolumeInfoField.capacity_bytes in storage_manager._exposed_volume_info

    if show_percentage or show_used or show_total:
        volume_usage_cache = await valkey_stat_client.get_volume_usage(proxy_name, volume_name)

        if volume_usage_cache:
            volume_usage = msgpack.unpackb(volume_usage_cache)
        else:
            manager_client = storage_manager.get_manager_facing_client(proxy_name)
            storage_reply = await manager_client.get_fs_usage(volume_name)
            storage_used_bytes = storage_reply[ExposedVolumeInfoField.used_bytes]
            storage_capacity_bytes = storage_reply[ExposedVolumeInfoField.capacity_bytes]

            if show_used:
                volume_usage["used"] = storage_used_bytes

            if show_total:
                volume_usage["total"] = storage_capacity_bytes

            if show_percentage:
                try:
                    volume_usage["percentage"] = (storage_used_bytes / storage_capacity_bytes) * 100
                except ZeroDivisionError:
                    volume_usage["percentage"] = 0

            await valkey_stat_client.set_volume_usage(
                proxy_name, volume_name, msgpack.packb(volume_usage), 60
            )

    return volume_usage


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict({
        tx.AliasedKey(["group_id", "groupId"], default=None): tx.UUID | t.String | t.Null,
    }),
)
async def list_hosts(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    log.info(
        "VFOLDER.LIST_HOSTS (emai:{}, ak:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
    )
    domain_name = request["user"]["domain_name"]
    group_id = params["group_id"]
    resource_policy = request["keypair"]["resource_policy"]
    allowed_vfolder_types = (
        await root_ctx.config_provider.legacy_etcd_config_loader.get_vfolder_types()
    )
    async with root_ctx.db.begin() as conn:
        allowed_hosts = VFolderHostPermissionMap()
        if "user" in allowed_vfolder_types:
            allowed_hosts_by_user = await get_allowed_vfolder_hosts_by_user(
                conn, resource_policy, domain_name, request["user"]["uuid"], group_id
            )
            allowed_hosts = allowed_hosts | allowed_hosts_by_user
        if "group" in allowed_vfolder_types:
            allowed_hosts_by_group = await get_allowed_vfolder_hosts_by_group(
                conn,
                resource_policy,
                domain_name,
                group_id,
            )
            allowed_hosts = allowed_hosts | allowed_hosts_by_group
    all_volumes = await root_ctx.storage_manager.get_all_volumes()
    all_hosts = {f"{proxy_name}:{volume_data['name']}" for proxy_name, volume_data in all_volumes}
    allowed_hosts = VFolderHostPermissionMap({
        host: perms for host, perms in allowed_hosts.items() if host in all_hosts
    })

    default_host = root_ctx.config_provider.config.volumes.default_host
    if default_host not in allowed_hosts:
        default_host = None

    volumes = [
        (proxy_name, volume_data)
        for proxy_name, volume_data in all_volumes
        if f"{proxy_name}:{volume_data['name']}" in allowed_hosts
    ]

    fetch_exposed_volume_fields_tasks = [
        fetch_exposed_volume_fields(
            storage_manager=root_ctx.storage_manager,
            valkey_stat_client=root_ctx.valkey_stat,
            proxy_name=proxy_name,
            volume_name=volume_data["name"],
        )
        for proxy_name, volume_data in volumes
    ]
    get_sftp_scaling_groups_tasks = [
        root_ctx.storage_manager.get_sftp_scaling_groups(proxy_name)
        for proxy_name, volume_data in volumes
    ]

    fetch_exposed_volume_fields_results, get_sftp_scaling_groups_results = await asyncio.gather(
        asyncio.gather(*fetch_exposed_volume_fields_tasks),
        asyncio.gather(*get_sftp_scaling_groups_tasks),
    )

    volume_info = {
        f"{proxy_name}:{volume_data['name']}": {
            "backend": volume_data["backend"],
            "capabilities": volume_data["capabilities"],
            "usage": usage,
            "sftp_scaling_groups": sftp_scaling_groups,
        }
        for (proxy_name, volume_data), usage, sftp_scaling_groups in zip(
            volumes, fetch_exposed_volume_fields_results, get_sftp_scaling_groups_results
        )
    }
    resp = {
        "default": default_host,
        "allowed": sorted(allowed_hosts),
        "volume_info": volume_info,
    }
    return web.json_response(resp, status=HTTPStatus.OK)


@superadmin_required
@server_status_required(READ_ALLOWED)
async def list_all_hosts(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    log.info(
        "VFOLDER.LIST_ALL_HOSTS (email:{}, ak:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
    )
    all_volumes = await root_ctx.storage_manager.get_all_volumes()
    all_hosts = {f"{proxy_name}:{volume_data['name']}" for proxy_name, volume_data in all_volumes}
    default_host = root_ctx.config_provider.config.volumes.default_host
    if default_host not in all_hosts:
        default_host = None
    resp = {
        "default": default_host,
        "allowed": sorted(all_hosts),
    }
    return web.json_response(resp, status=HTTPStatus.OK)


@superadmin_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key("folder_host"): t.String,
    })
)
async def get_volume_perf_metric(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    log.info(
        "VFOLDER.VOLUME_PERF_METRIC (email:{}, ak:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
    )
    proxy_name, volume_name = root_ctx.storage_manager.get_proxy_and_volume(params["folder_host"])
    manager_client = root_ctx.storage_manager.get_manager_facing_client(proxy_name)
    storage_reply = await manager_client.get_volume_performance_metric(volume_name)
    return web.json_response(storage_reply, status=HTTPStatus.OK)


@auth_required
@server_status_required(READ_ALLOWED)
async def list_allowed_types(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    log.info(
        "VFOLDER.LIST_ALLOWED_TYPES (email:{}, ak:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
    )
    allowed_vfolder_types = (
        await root_ctx.config_provider.legacy_etcd_config_loader.get_vfolder_types()
    )
    return web.json_response(allowed_vfolder_types, status=HTTPStatus.OK)


@auth_required
@server_status_required(READ_ALLOWED)
@with_vfolder_rows_resolved(VFolderPermissionSetAlias.READABLE)
@with_vfolder_status_checked(VFolderStatusSet.READABLE)
async def get_info(request: web.Request, row: VFolderRow) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    log.info(
        "VFOLDER.GETINFO (email:{}, ak:{}, vf:{} (resolved-from:{!r}))",
        request["user"]["email"],
        request["keypair"]["access_key"],
        row["id"],
        request.match_info["name"],
    )
    result = await root_ctx.processors.vfolder.get_vfolder.wait_for_complete(
        GetVFolderAction(
            request["user"]["uuid"],
            vfolder_uuid=row["id"],
        )
    )
    resp = {
        "name": result.base_info.name,
        "id": result.base_info.id.hex,
        "quota_scope_id": str(result.base_info.quota_scope_id),
        "host": result.base_info.host,
        "status": result.base_info.status,
        "num_files": result.usage_info.num_files,
        "used_bytes": result.usage_info.used_bytes,
        "created_at": str(result.base_info.created_at),
        "last_used": str(result.base_info.created_at),
        "user": str(result.ownership_info.user_uuid) if result.ownership_info.user_uuid else None,
        "group": str(result.ownership_info.group_uuid)
        if result.ownership_info.group_uuid
        else None,
        "type": "user" if result.ownership_info.user_uuid else "group",
        "is_owner": result.ownership_info.is_owner,
        "permission": result.base_info.mount_permission.value,
        "usage_mode": result.base_info.usage_mode.value,
        "cloneable": result.base_info.cloneable,
    }
    return web.json_response(resp, status=HTTPStatus.OK)


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key("folder_host"): t.String,
        t.Key("id"): tx.UUID,
    })
)
async def get_quota(request: web.Request, params: Any) -> web.Response:
    vfolder_row = (
        await resolve_vfolder_rows(request, VFolderPermissionSetAlias.READABLE, params["id"])
    )[0]
    await check_vfolder_status(vfolder_row, VFolderStatusSet.READABLE)
    root_ctx: RootContext = request.app["_root.context"]
    proxy_name, volume_name = root_ctx.storage_manager.get_proxy_and_volume(
        params["folder_host"], is_unmanaged(vfolder_row["unmanaged_path"])
    )
    log.info(
        "VFOLDER.GET_QUOTA (email:{}, volume_name:{}, vf:{})",
        request["user"]["email"],
        volume_name,
        params["id"],
    )

    # Permission check for the requested vfolder.
    user_role = request["user"]["role"]
    user_uuid = request["user"]["uuid"]
    domain_name = request["user"]["domain_name"]
    if user_role == UserRole.SUPERADMIN:
        pass
    else:
        allowed_vfolder_types = (
            await root_ctx.config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )
        async with root_ctx.db.begin_readonly() as conn:
            extra_vf_conds = [vfolders.c.id == params["id"]]
            entries = await query_accessible_vfolders(
                conn,
                user_uuid,
                user_role=user_role,
                domain_name=domain_name,
                allowed_vfolder_types=allowed_vfolder_types,
                extra_vf_conds=(sa.and_(*extra_vf_conds)),
            )
        if len(entries) == 0:
            raise VFolderNotFound(extra_data=params["id"])

    manager_client = root_ctx.storage_manager.get_manager_facing_client(proxy_name)
    vfid = str(VFolderID.from_row(vfolder_row))
    # Get quota for the specific vfolder
    storage_reply = await manager_client.get_volume_quota(volume_name, vfid)
    return web.json_response(storage_reply, status=HTTPStatus.OK)


@auth_required
@server_status_required(ALL_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key("folder_host"): t.String,
        t.Key("id"): tx.UUID,
        t.Key("input"): t.Mapping(t.String, t.Any),
    }),
)
async def update_quota(request: web.Request, params: Any) -> web.Response:
    vfolder_row = (
        await resolve_vfolder_rows(request, VFolderPermissionSetAlias.READABLE, params["id"])
    )[0]
    await check_vfolder_status(vfolder_row, VFolderStatusSet.READABLE)
    root_ctx: RootContext = request.app["_root.context"]
    folder_host = params["folder_host"]
    proxy_name, volume_name = root_ctx.storage_manager.get_proxy_and_volume(
        folder_host, is_unmanaged(vfolder_row["unmanaged_path"])
    )
    quota = int(params["input"]["size_bytes"])
    log.info(
        "VFOLDER.UPDATE_QUOTA (email:{}, volume_name:{}, quota:{}, vf:{})",
        request["user"]["email"],
        volume_name,
        quota,
        params["id"],
    )

    # Permission check for the requested vfolder.
    user_role = request["user"]["role"]
    user_uuid = request["user"]["uuid"]
    domain_name = request["user"]["domain_name"]
    resource_policy = request["keypair"]["resource_policy"]

    if user_role == UserRole.SUPERADMIN:
        pass
    else:
        allowed_vfolder_types = (
            await root_ctx.config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )
        async with root_ctx.db.begin_readonly() as conn:
            await ensure_host_permission_allowed(
                conn,
                folder_host,
                allowed_vfolder_types=allowed_vfolder_types,
                user_uuid=user_uuid,
                resource_policy=resource_policy,
                domain_name=domain_name,
                permission=VFolderHostPermission.MODIFY,
            )
            extra_vf_conds = [vfolders.c.id == params["id"]]
            entries = await query_accessible_vfolders(
                conn,
                user_uuid,
                user_role=user_role,
                domain_name=domain_name,
                allowed_vfolder_types=allowed_vfolder_types,
                extra_vf_conds=(sa.and_(*extra_vf_conds)),
            )
        if len(entries) == 0:
            raise VFolderNotFound(extra_data=params["id"])

    # Limit vfolder size quota if it is larger than max_quota_scope_size of the resource policy.
    max_quota_scope_size = resource_policy.get("max_quota_scope_size", 0)
    if max_quota_scope_size > 0 and (quota <= 0 or quota > max_quota_scope_size):
        quota = max_quota_scope_size

    manager_client = root_ctx.storage_manager.get_manager_facing_client(proxy_name)
    vfid = str(VFolderID.from_row(vfolder_row))
    # Update quota scope with new quota value
    await manager_client.update_volume_quota(volume_name, vfid, quota)

    # Update the quota for the vfolder in DB.
    async with root_ctx.db.begin() as conn:
        query = (
            sa.update(vfolders)
            .values(max_size=math.ceil(quota / 2**20))  # in Mbytes
            .where(vfolders.c.id == params["id"])
        )
        result = await conn.execute(query)
        assert result.rowcount == 1

    return web.json_response({"size_bytes": quota}, status=HTTPStatus.OK)


@superadmin_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key("folder_host"): t.String,
        t.Key("id"): tx.UUID,
    })
)
async def get_usage(request: web.Request, params: Any) -> web.Response:
    vfolder_row = (
        await resolve_vfolder_rows(request, VFolderPermissionSetAlias.READABLE, params["id"])
    )[0]
    await check_vfolder_status(vfolder_row, VFolderStatusSet.READABLE)
    root_ctx: RootContext = request.app["_root.context"]
    proxy_name, volume_name = root_ctx.storage_manager.get_proxy_and_volume(
        params["folder_host"], is_unmanaged(vfolder_row["unmanaged_path"])
    )
    log.info(
        "VFOLDER.GET_USAGE (email:{}, volume_name:{}, vf:{})",
        request["user"]["email"],
        volume_name,
        params["id"],
    )
    client = root_ctx.storage_manager.get_manager_facing_client(proxy_name)
    vfid = str(VFolderID(vfolder_row["quota_scope_id"], params["id"]))
    usage = await client.get_folder_usage(volume_name, vfid)
    return web.json_response(usage, status=HTTPStatus.OK)


@superadmin_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key("folder_host"): t.String,
        t.Key("id"): tx.UUID,
    })
)
async def get_used_bytes(request: web.Request, params: Any) -> web.Response:
    vfolder_row = (
        await resolve_vfolder_rows(request, VFolderPermissionSetAlias.READABLE, params["id"])
    )[0]
    await check_vfolder_status(vfolder_row, VFolderStatusSet.READABLE)
    root_ctx: RootContext = request.app["_root.context"]
    proxy_name, volume_name = root_ctx.storage_manager.get_proxy_and_volume(
        params["folder_host"], is_unmanaged(vfolder_row["unmanaged_path"])
    )
    log.info("VFOLDER.GET_USED_BYTES (volume_name:{}, vf:{})", volume_name, params["id"])
    client = root_ctx.storage_manager.get_manager_facing_client(proxy_name)
    vfid = str(VFolderID(vfolder_row["quota_scope_id"], params["id"]))
    usage = await client.get_used_bytes(volume_name, vfid)
    return web.json_response(usage, status=HTTPStatus.OK)


class RenameRequestModel(LegacyBaseRequestModel):
    new_name: tv.VFolderName = Field(
        description="Name of the vfolder",
    )

    def to_modifier(self) -> VFolderAttributeModifier:
        return VFolderAttributeModifier(
            name=OptionalState[str].update(self.new_name),
        )


@auth_required
@server_status_required(ALL_ALLOWED)
@pydantic_params_api_handler(RenameRequestModel)  # type: ignore  # FIXME: remove after vfolder refactoring
@with_vfolder_rows_resolved(VFolderPermission.OWNER_PERM)
@with_vfolder_status_checked(VFolderStatusSet.READABLE)
async def rename_vfolder(
    request: web.Request,
    row: VFolderRow,
    params: RenameRequestModel,
) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    new_name = params.new_name
    log.info(
        "VFOLDER.RENAME (email:{}, ak:{}, vf:{} (resolved-from:{!r}), new-name:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
        row["id"],
        request.match_info["name"],
        new_name,
    )

    await root_ctx.processors.vfolder.update_vfolder_attribute.wait_for_complete(
        UpdateVFolderAttributeAction(
            user_uuid=request["user"]["uuid"],
            vfolder_uuid=row["id"],
            modifier=params.to_modifier(),
        )
    )
    return web.Response(status=HTTPStatus.CREATED)


@auth_required
@server_status_required(ALL_ALLOWED)
@with_vfolder_rows_resolved(VFolderPermission.OWNER_PERM)
@with_vfolder_status_checked(VFolderStatusSet.UPDATABLE)
@check_api_params(
    t.Dict({
        t.Key("cloneable", default=None): t.Bool | t.Null,
        t.Key("permission", default=None): tx.Enum(VFolderPermission) | t.Null,
    })
)
async def update_vfolder_options(
    request: web.Request, params: Any, row: VFolderRow
) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    log.info(
        "VFOLDER.UPDATE_OPTIONS (email:{}, ak:{}, vf:{} (resolved-from:{!r}))",
        request["user"]["email"],
        request["keypair"]["access_key"],
        row["id"],
        request.match_info["name"],
    )
    cloneable = (
        OptionalState[bool].update(params["cloneable"])
        if params["cloneable"] is not None
        else OptionalState[bool].nop()
    )
    mount_permission = (
        OptionalState[VFolderPermission].update(params["permission"])
        if params["permission"] is not None
        else OptionalState[VFolderPermission].nop()
    )
    await root_ctx.processors.vfolder.update_vfolder_attribute.wait_for_complete(
        UpdateVFolderAttributeAction(
            user_uuid=request["user"]["uuid"],
            vfolder_uuid=row["id"],
            modifier=VFolderAttributeModifier(
                cloneable=cloneable,
                mount_permission=mount_permission,
            ),
        )
    )
    return web.Response(status=HTTPStatus.CREATED)


@auth_required
@server_status_required(READ_ALLOWED)
@with_vfolder_rows_resolved(VFolderPermissionSetAlias.WRITABLE)
@with_vfolder_status_checked(VFolderStatusSet.UPDATABLE)
@check_api_params(
    t.Dict({
        t.Key("path"): t.String | t.List(t.String),
        t.Key("parents", default=True): t.ToBool,
        t.Key("exist_ok", default=False): t.ToBool,
    })
)
async def mkdir(request: web.Request, params: Any, row: VFolderRow) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    log.info(
        "VFOLDER.MKDIR (email:{}, ak:{}, vf:{} (resolved-from:{!r}), paths:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
        row["id"],
        request.match_info["name"],
        params["path"],
    )

    result = await root_ctx.processors.vfolder_file.mkdir.wait_for_complete(
        MkdirAction(
            user_id=request["user"]["uuid"],
            vfolder_uuid=row["id"],
            path=params["path"],
            parents=params["parents"],
            exist_ok=params["exist_ok"],
        )
    )
    return web.json_response({"results": result.results}, status=result.storage_resp_status)


@auth_required
@server_status_required(READ_ALLOWED)
@with_vfolder_rows_resolved(VFolderPermissionSetAlias.READABLE)
@with_vfolder_status_checked(VFolderStatusSet.READABLE)
@check_api_params(
    t.Dict({
        tx.AliasedKey(["path", "file"]): t.String,
        t.Key("archive", default=False): t.ToBool,
    })
)
async def create_download_session(
    request: web.Request, params: Any, row: VFolderRow
) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    log.info(
        "VFOLDER.CREATE_DOWNLOAD_SESSION(email:{}, ak:{}, vf:{} (resolved-from:{!r}), path:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
        row["id"],
        request.match_info["name"],
        params["path"],
    )
    result = await root_ctx.processors.vfolder_file.download_file.wait_for_complete(
        CreateDownloadSessionAction(
            user_uuid=request["user"]["uuid"],
            keypair_resource_policy=request["keypair"]["resource_policy"],
            vfolder_uuid=row["id"],
            path=params["path"],
            archive=params["archive"],
        )
    )
    resp = {"token": result.token, "url": result.url}
    return web.json_response(resp, status=HTTPStatus.OK)


@auth_required
@server_status_required(READ_ALLOWED)
@with_vfolder_rows_resolved(VFolderPermissionSetAlias.WRITABLE)
@with_vfolder_status_checked(VFolderStatusSet.UPDATABLE)
@check_api_params(
    t.Dict({
        t.Key("path"): t.String,
        t.Key("size"): t.ToInt,
    })
)
async def create_upload_session(request: web.Request, params: Any, row: VFolderRow) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    log.info(
        "VFOLDER.CREATE_UPLOAD_SESSION (email:{}, ak:{}, vf:{} (resolved-from:{!r}), path:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
        row["id"],
        request.match_info["name"],
        params["path"],
    )
    result = await root_ctx.processors.vfolder_file.upload_file.wait_for_complete(
        CreateUploadSessionAction(
            user_uuid=request["user"]["uuid"],
            keypair_resource_policy=request["keypair"]["resource_policy"],
            vfolder_uuid=row["id"],
            path=params["path"],
            size=params["size"],
        )
    )
    resp = {"token": result.token, "url": result.url}
    return web.json_response(resp, status=HTTPStatus.OK)


@auth_required
@server_status_required(READ_ALLOWED)
@with_vfolder_rows_resolved(VFolderPermissionSetAlias.WRITABLE)
@with_vfolder_status_checked(VFolderStatusSet.UPDATABLE)
@check_api_params(
    t.Dict({
        t.Key("target_path"): t.String,
        t.Key("new_name"): t.String,
        t.Key("is_dir", default=False): t.ToBool,  # ignored since 22.03
    })
)
async def rename_file(request: web.Request, params: Any, row: VFolderRow) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    log.info(
        "VFOLDER.RENAME_FILE (email:{}, ak:{}, vf:{} (resolved-from:{!r}), target_path:{}, new_name:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
        row["id"],
        request.match_info["name"],
        params["target_path"],
        params["new_name"],
    )
    await root_ctx.processors.vfolder_file.rename_file.wait_for_complete(
        RenameFileAction(
            user_uuid=request["user"]["uuid"],
            keypair_resource_policy=request["keypair"]["resource_policy"],
            vfolder_uuid=row["id"],
            target_path=params["target_path"],
            new_name=params["new_name"],
        )
    )
    return web.json_response({}, status=HTTPStatus.OK)


@auth_required
@server_status_required(READ_ALLOWED)
@with_vfolder_rows_resolved(VFolderPermissionSetAlias.WRITABLE)
@with_vfolder_status_checked(VFolderStatusSet.UPDATABLE)
@check_api_params(
    t.Dict({
        t.Key("src"): t.String,
        t.Key("dst"): t.String,
    })
)
async def move_file(request: web.Request, params: Any, row: VFolderRow) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    log.info(
        "VFOLDER.MOVE_FILE (email:{}, ak:{}, vf:{} (resolved-from:{!r}), src:{}, dst:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
        row["id"],
        request.match_info["name"],
        params["src"],
        params["dst"],
    )
    proxy_name, volume_name = root_ctx.storage_manager.get_proxy_and_volume(
        row["host"], is_unmanaged(row["unmanaged_path"])
    )
    manager_client = root_ctx.storage_manager.get_manager_facing_client(proxy_name)
    vfid = str(VFolderID(row["quota_scope_id"], row["id"]))
    await manager_client.move_file(volume_name, vfid, params["src"], params["dst"])
    return web.json_response({}, status=HTTPStatus.OK)


@auth_required
@server_status_required(READ_ALLOWED)
@with_vfolder_rows_resolved(VFolderPermissionSetAlias.WRITABLE)
@with_vfolder_status_checked(VFolderStatusSet.UPDATABLE)
@check_api_params(
    t.Dict({
        t.Key("files"): t.List(t.String),
        t.Key("recursive", default=False): t.ToBool,
    })
)
async def delete_files(request: web.Request, params: Any, row: VFolderRow) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    recursive = params["recursive"]
    log.info(
        "VFOLDER.DELETE_FILES (email:{}, ak:{}, vf:{} (resolved-from:{!r}), path:{}, recursive:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
        row["id"],
        request.match_info["name"],
        params["files"],
        recursive,
    )
    await root_ctx.processors.vfolder_file.delete_files.wait_for_complete(
        DeleteFilesAction(
            user_uuid=request["user"]["uuid"],
            vfolder_uuid=row["id"],
            files=params["files"],
            recursive=recursive,
        )
    )
    return web.json_response({}, status=HTTPStatus.OK)


@auth_required
@server_status_required(READ_ALLOWED)
@with_vfolder_rows_resolved(VFolderPermissionSetAlias.READABLE)
@with_vfolder_status_checked(VFolderStatusSet.READABLE)
@check_api_params(
    t.Dict({
        t.Key("path", default=""): t.String(allow_blank=True),
    })
)
async def list_files(request: web.Request, params: Any, row: VFolderRow) -> web.Response:
    # we can skip check_vfolder_status() guard here since the status is already verified by
    # vfolder_permission_required() decorator
    root_ctx: RootContext = request.app["_root.context"]
    log.info(
        "VFOLDER.LIST_FILES (email:{}, ak:{}, vf:{} (resolved-from:{!r}), path:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
        row["id"],
        request.match_info["name"],
        params["path"],
    )
    result = await root_ctx.processors.vfolder_file.list_files.wait_for_complete(
        ListFilesAction(
            user_uuid=request["user"]["uuid"],
            vfolder_uuid=row["id"],
            path=params["path"],
        )
    )
    resp = {
        "items": [info.to_json() for info in result.files],
    }
    return web.json_response(resp, status=HTTPStatus.OK)


@auth_required
@server_status_required(READ_ALLOWED)
async def list_sent_invitations(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    log.info(
        "VFOLDER.LIST_SENT_INVITATIONS (email:{}, ak:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
    )
    async with root_ctx.db.begin() as conn:
        j = sa.join(vfolders, vfolder_invitations, vfolders.c.id == vfolder_invitations.c.vfolder)
        query = (
            sa.select([vfolder_invitations, vfolders.c.name])
            .select_from(j)
            .where(
                (vfolder_invitations.c.inviter == request["user"]["email"])
                & (vfolder_invitations.c.state == VFolderInvitationState.PENDING),
            )
        )
        result = await conn.execute(query)
        invitations = result.fetchall()
    invs_info = []
    for inv in invitations:
        invs_info.append({
            "id": str(inv.id),
            "inviter": inv.inviter,
            "invitee": inv.invitee,
            "perm": inv.permission,
            "state": inv.state.value,
            "created_at": str(inv.created_at),
            "modified_at": str(inv.modified_at),
            "vfolder_id": str(inv.vfolder),
            "vfolder_name": inv.name,
        })
    resp = {"invitations": invs_info}
    return web.json_response(resp, status=HTTPStatus.OK)


@auth_required
@server_status_required(ALL_ALLOWED)
@check_api_params(
    t.Dict({
        tx.AliasedKey(["perm", "permission"]): VFolderPermissionValidator,
    }),
)
async def update_invitation(request: web.Request, params: Any) -> web.Response:
    """
    Update sent invitation's permission. Other fields are not allowed to be updated.
    """
    root_ctx: RootContext = request.app["_root.context"]
    inv_id = request.match_info["inv_id"]
    log.info(
        "VFOLDER.UPDATE_INVITATION (email:{}, ak:{}, inv:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
        inv_id,
    )
    await root_ctx.processors.vfolder_invite.update_invitation.wait_for_complete(
        UpdateInvitationAction(
            invitation_id=uuid.UUID(inv_id),
            requester_user_uuid=request["user"]["uuid"],
            mount_permission=params["perm"],
        )
    )
    resp = {"msg": f"vfolder invitation updated: {inv_id}."}
    return web.json_response(resp, status=HTTPStatus.OK)


@auth_required
@server_status_required(ALL_ALLOWED)
@with_vfolder_rows_resolved(VFolderPermission.OWNER_PERM)
@with_vfolder_status_checked(VFolderStatusSet.UPDATABLE)
@check_api_params(
    t.Dict({
        tx.AliasedKey(["perm", "permission"], default="rw"): VFolderPermissionValidator,
        tx.AliasedKey(["emails", "user_ids", "userIDs"]): t.List(t.String),
    }),
)
async def invite(request: web.Request, params: Any, row: VFolderRow) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    user_uuid = request["user"]["uuid"]
    perm = params["perm"]
    invitee_emails = params["emails"]
    log.info(
        "VFOLDER.INVITE (email:{}, ak:{}, vf:{} (resolved-from:{!r}), inv.users:{})",
        request["user"]["email"],
        access_key,
        row["id"],
        request.match_info["name"],
        ",".join(invitee_emails),
    )
    async with root_ctx.db.begin_readonly_session() as db_session:
        user_rows = await db_session.scalars(
            sa.select(UserRow).where(UserRow.email.in_(invitee_emails))
        )
        user_uuids = [row.uuid for row in user_rows]
    if not user_uuids:
        raise VFolderNotFound("No users found with the provided emails.")
    result = await root_ctx.processors.vfolder_invite.invite_vfolder.wait_for_complete(
        InviteVFolderAction(
            keypair_resource_policy=request["keypair"]["resource_policy"],
            user_uuid=user_uuid,
            vfolder_uuid=row["id"],
            mount_permission=perm,
            invitee_user_uuids=user_uuids,
        )
    )
    resp = {"invited_ids": result.invitation_ids}
    return web.json_response(resp, status=HTTPStatus.CREATED)


@auth_required
@server_status_required(READ_ALLOWED)
async def invitations(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    log.info(
        "VFOLDER.INVITATIONS (email:{}, ak:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
    )
    result = await root_ctx.processors.vfolder_invite.list_invitation.wait_for_complete(
        ListInvitationAction(
            requester_user_uuid=request["user"]["uuid"],
        )
    )
    resp = {
        "invitations": [
            {**info.to_json(), "perm": info.mount_permission.value} for info in result.info
        ]
    }
    return web.json_response(resp, status=HTTPStatus.OK)


@auth_required
@server_status_required(ALL_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key("inv_id"): t.String,
    }),
)
async def accept_invitation(request: web.Request, params: Any) -> web.Response:
    """Accept invitation by invitee.

    * `inv_ak` parameter is removed from 19.06 since virtual folder's ownership is
    moved from keypair to a user or a group.

    :param inv_id: ID of vfolder_invitations row.
    """
    root_ctx: RootContext = request.app["_root.context"]
    inv_id = params["inv_id"]
    log.info(
        "VFOLDER.ACCEPT_INVITATION (email:{}, ak:{}, inv:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
        inv_id,
    )
    await root_ctx.processors.vfolder_invite.accept_invitation.wait_for_complete(
        AcceptInvitationAction(
            invitation_id=inv_id,
        )
    )
    return web.json_response({})


@auth_required
@server_status_required(ALL_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key("inv_id"): t.String,
    })
)
async def delete_invitation(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    inv_id = params["inv_id"]
    log.info(
        "VFOLDER.DELETE_INVITATION (email:{}, ak:{}, inv:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
        inv_id,
    )
    await root_ctx.processors.vfolder_invite.reject_invitation.wait_for_complete(
        RejectInvitationAction(
            invitation_id=inv_id,
            requester_user_uuid=request["user"]["uuid"],
        )
    )
    return web.json_response({})


@admin_required
@server_status_required(ALL_ALLOWED)
@with_vfolder_rows_resolved(VFolderPermission.READ_ONLY)
@with_vfolder_status_checked(VFolderStatusSet.UPDATABLE)
@check_api_params(
    t.Dict({
        t.Key("permission", default="rw"): VFolderPermissionValidator,
        t.Key("emails"): t.List(t.String),
    }),
)
async def share(request: web.Request, params: Any, row: VFolderRow) -> web.Response:
    """
    Share a group folder to users with overriding permission.

    This will create vfolder_permission(s) relation directly without
    creating invitation(s). Only group-type vfolders are allowed to
    be shared directly.
    """
    root_ctx: RootContext = request.app["_root.context"]
    log.info(
        "VFOLDER.SHARE (email:{}, ak:{}, vf:{} (resolved-from:{!r}), perm:{}, users:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
        row["id"],
        request.match_info["name"],
        params["permission"],
        ",".join(params["emails"]),
    )
    user_uuid = request["user"]["uuid"]
    domain_name = request["user"]["domain_name"]
    resource_policy = request["keypair"]["resource_policy"]
    if row["ownership_type"] != VFolderOwnershipType.GROUP:
        raise VFolderNotFound("Only project folders are directly sharable.")
    async with root_ctx.db.begin() as conn:
        from ..models import association_groups_users as agus

        allowed_vfolder_types = (
            await root_ctx.config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )
        await ensure_host_permission_allowed(
            conn,
            row["host"],
            allowed_vfolder_types=allowed_vfolder_types,
            user_uuid=user_uuid,
            resource_policy=resource_policy,
            domain_name=domain_name,
            permission=VFolderHostPermission.SET_USER_PERM,
        )

        # Convert users' emails to uuids and check if user belong to the group of vfolder.
        j = users.join(agus, users.c.uuid == agus.c.user_id)
        query = (
            sa.select([users.c.uuid, users.c.email])
            .select_from(j)
            .where(
                (users.c.email.in_(params["emails"]))
                & (users.c.email != request["user"]["email"])
                & (agus.c.group_id == row["group"])
                & (users.c.status.in_(ACTIVE_USER_STATUSES)),
            )
        )
        result = await conn.execute(query)
        user_info = result.fetchall()
        users_to_share = [u["uuid"] for u in user_info]
        emails_to_share = [u["email"] for u in user_info]
        if len(user_info) < 1:
            raise ObjectNotFound(object_name="user")
        if len(user_info) < len(params["emails"]):
            users_not_invfolder_group = list(set(params["emails"]) - set(emails_to_share))
            raise ObjectNotFound(
                "Some users do not belong to folder's group:"
                f" {','.join(users_not_invfolder_group)}",
                object_name="user",
            )

        # Do not share to users who have already been shared the folder.
        query = (
            sa.select([vfolder_permissions])
            .select_from(vfolder_permissions)
            .where(
                (vfolder_permissions.c.user.in_(users_to_share))
                & (vfolder_permissions.c.vfolder == row["id"]),
            )
        )
        result = await conn.execute(query)
        users_not_to_share = [u.user for u in result.fetchall()]
        users_to_share = list(set(users_to_share) - set(users_not_to_share))

        # Create vfolder_permission(s).
        for _user in users_to_share:
            query = sa.insert(
                vfolder_permissions,
                {
                    "permission": params["permission"],
                    "vfolder": row["id"],
                    "user": _user,
                },
            )
            await conn.execute(query)
        # Update existing vfolder_permission(s).
        for _user in users_not_to_share:
            query = (
                sa.update(vfolder_permissions)
                .values(permission=params["permission"])
                .where(vfolder_permissions.c.vfolder == row["id"])
                .where(vfolder_permissions.c.user == _user)
            )
            await conn.execute(query)

        return web.json_response({"shared_emails": emails_to_share}, status=HTTPStatus.CREATED)


@admin_required
@server_status_required(ALL_ALLOWED)
@with_vfolder_rows_resolved(VFolderPermission.READ_ONLY)
@with_vfolder_status_checked(VFolderStatusSet.UPDATABLE)
@check_api_params(
    t.Dict({
        t.Key("emails"): t.List(t.String),
    }),
)
async def unshare(request: web.Request, params: Any, row: VFolderRow) -> web.Response:
    """
    Unshare a group folder from users.
    """
    root_ctx: RootContext = request.app["_root.context"]
    log.info(
        "VFOLDER.UNSHARE (email:{}, ak:{}, vf:{} (resolved-from:{!r}), users:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
        row["id"],
        request.match_info["name"],
        ",".join(params["emails"]),
    )
    user_uuid = request["user"]["uuid"]
    domain_name = request["user"]["domain_name"]
    resource_policy = request["keypair"]["resource_policy"]
    if row["ownership_type"] != VFolderOwnershipType.GROUP:
        raise VFolderNotFound("Only project folders are directly unsharable.")
    async with root_ctx.db.begin() as conn:
        allowed_vfolder_types = (
            await root_ctx.config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )
        await ensure_host_permission_allowed(
            conn,
            row["host"],
            allowed_vfolder_types=allowed_vfolder_types,
            user_uuid=user_uuid,
            resource_policy=resource_policy,
            domain_name=domain_name,
            permission=VFolderHostPermission.SET_USER_PERM,
        )

        # Convert users' emails to uuids.
        query = (
            sa.select([users.c.uuid]).select_from(users).where(users.c.email.in_(params["emails"]))
        )
        result = await conn.execute(query)
        users_to_unshare = [u["uuid"] for u in result.fetchall()]
        if len(users_to_unshare) < 1:
            raise ObjectNotFound(object_name="user(s).")

        # Delete vfolder_permission(s).
        query = sa.delete(vfolder_permissions).where(
            (vfolder_permissions.c.vfolder == row["id"])
            & (vfolder_permissions.c.user.in_(users_to_unshare)),
        )
        await conn.execute(query)
        return web.json_response({"unshared_emails": params["emails"]}, status=HTTPStatus.OK)


async def _delete(
    root_ctx: RootContext,
    vfolder_row: VFolderRow,
    user_uuid: uuid.UUID,
    user_role: UserRole,
    domain_name: str,
    resource_policy: Mapping[str, Any],
) -> None:
    # Only the effective folder owner can delete the folder.
    if not vfolder_row["is_owner"]:
        raise InvalidAPIParameters("Cannot delete the vfolder that is not owned by myself.")
    await check_vfolder_status(vfolder_row, VFolderStatusSet.DELETABLE)
    async with root_ctx.db.begin_readonly_session() as db_session:
        # perform extra check to make sure records of alive model service not removed by foreign key rule
        if vfolder_row["usage_mode"] == VFolderUsageMode.MODEL:
            live_endpoints = await EndpointRow.list_by_model(db_session, vfolder_row["id"])
            if (
                len([e for e in live_endpoints if e.lifecycle_stage == EndpointLifecycle.CREATED])
                > 0
            ):
                raise ModelServiceDependencyNotCleared
        folder_host = vfolder_row["host"]
        allowed_vfolder_types = (
            await root_ctx.config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )
        await ensure_host_permission_allowed(
            db_session.bind,
            folder_host,
            allowed_vfolder_types=allowed_vfolder_types,
            user_uuid=user_uuid,
            resource_policy=resource_policy,
            domain_name=domain_name,
            permission=VFolderHostPermission.DELETE,
        )

    vfolder_row_ids = (vfolder_row["id"],)
    async with root_ctx.db.connect() as db_conn:
        await delete_vfolder_relation_rows(db_conn, root_ctx.db.begin_session, vfolder_row_ids)
    await update_vfolder_status(
        root_ctx.db,
        vfolder_row_ids,
        VFolderOperationStatus.DELETE_PENDING,
    )


class DeleteRequestModel(LegacyBaseRequestModel):
    vfolder_id: uuid.UUID = Field(
        validation_alias=AliasChoices("vfolderId", "id"),
        description="Target vfolder id to soft-delete, to go to trash bin",
    )


@auth_required
@server_status_required(ALL_ALLOWED)
@pydantic_params_api_handler(DeleteRequestModel)
async def delete_by_id(request: web.Request, params: DeleteRequestModel) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]

    user_uuid = request["user"]["uuid"]
    resource_policy = request["keypair"]["resource_policy"]
    folder_id = params.vfolder_id

    log.info(
        "VFOLDER.DELETE_BY_ID (email:{}, ak:{}, vf:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
        folder_id,
    )
    try:
        await root_ctx.processors.vfolder.move_to_trash_vfolder.wait_for_complete(
            MoveToTrashVFolderAction(
                user_uuid=user_uuid,
                keypair_resource_policy=resource_policy,
                vfolder_uuid=folder_id,
            )
        )
    except VFolderInvalidParameter as e:
        raise InvalidAPIParameters(str(e))
    except VFolderMountedOnModelService:
        raise ModelServiceDependencyNotCleared()
    return web.Response(status=HTTPStatus.NO_CONTENT)


@auth_required
@server_status_required(ALL_ALLOWED)
async def delete_by_name(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]

    domain_name = request["user"]["domain_name"]
    user_role = request["user"]["role"]
    user_uuid = request["user"]["uuid"]
    resource_policy = request["keypair"]["resource_policy"]
    folder_name = request.match_info["name"]

    rows = await resolve_vfolder_rows(
        request,
        VFolderPermissionSetAlias.READABLE,
        folder_name,
        allow_privileged_access=True,
    )
    if len(rows) > 1:
        raise TooManyVFoldersFound(rows)
    row = rows[0]
    log.info(
        "VFOLDER.DELETE_BY_NAME (email:{}, ak:{}, vf:{} (resolved-from:{!r}))",
        request["user"]["email"],
        request["keypair"]["access_key"],
        row["id"],
        folder_name,
    )
    await _delete(
        root_ctx,
        row,
        user_uuid,
        user_role,
        domain_name,
        resource_policy,
    )
    return web.Response(status=HTTPStatus.NO_CONTENT)


class IDRequestModel(LegacyBaseRequestModel):
    name: str = Field(
        validation_alias=AliasChoices("vfolder_name", "vfolderName"),
        description="Target vfolder name",
    )


class CompactVFolderInfoModel(LegacyBaseResponseModel):
    id: uuid.UUID = Field(description="Unique ID referencing the vfolder.")
    name: str = Field(description="Name of the vfolder.")


@auth_required
@server_status_required(ALL_ALLOWED)
@pydantic_params_api_handler(IDRequestModel)
async def get_vfolder_id(request: web.Request, params: IDRequestModel) -> CompactVFolderInfoModel:
    folder_name = params.name
    rows = await resolve_vfolder_rows(
        request,
        VFolderPermissionSetAlias.READABLE,
        folder_name,
        allow_privileged_access=True,
    )
    if len(rows) > 1:
        raise TooManyVFoldersFound(rows)
    row = rows[0]
    log.info(
        "VFOLDER.GET_ID (email:{}, ak:{}, vf:{} (resolved-from:{!r}))",
        request["user"]["email"],
        request["keypair"]["access_key"],
        row["id"],
        folder_name,
    )
    return CompactVFolderInfoModel(id=row["id"], name=folder_name)


class DeleteFromTrashRequestModel(LegacyBaseRequestModel):
    vfolder_id: uuid.UUID = Field(
        validation_alias=AliasChoices("id", "vfolderId"),
        description="Target vfolder id to hard-delete, permanently remove from storage",
    )


@auth_required
@pydantic_params_api_handler(DeleteFromTrashRequestModel)
async def delete_from_trash_bin(
    request: web.Request, params: DeleteFromTrashRequestModel
) -> web.Response:
    """
    Delete `delete-pending` vfolders in storage proxy
    """
    root_ctx: RootContext = request.app["_root.context"]
    folder_id = params.vfolder_id
    user_uuid = request["user"]["uuid"]

    log.info(
        "VFOLDER.DELETE_FROM_TRASH_BIN (email:{}, ak:{}, vf:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
        folder_id,
    )
    try:
        await root_ctx.processors.vfolder.delete_forever_vfolder.wait_for_complete(
            DeleteForeverVFolderAction(
                user_uuid=user_uuid,
                vfolder_uuid=folder_id,
            )
        )
    except VFolderInvalidParameter as e:
        raise InvalidAPIParameters(str(e))
    except TooManyVFoldersFound:
        raise InternalServerError("Too many vfolders found")
    return web.Response(status=HTTPStatus.NO_CONTENT)


@auth_required
@server_status_required(ALL_ALLOWED)
async def force_delete(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]

    piece = request.match_info["folder_id"]
    try:
        folder_id = uuid.UUID(piece)
    except ValueError:
        log.error(f"Not allowed UUID type value ({piece})")
        return web.Response(status=HTTPStatus.BAD_REQUEST)

    await root_ctx.processors.vfolder.force_delete_vfolder.wait_for_complete(
        ForceDeleteVFolderAction(
            user_uuid=request["user"]["uuid"],
            vfolder_uuid=folder_id,
        )
    )
    return web.Response(status=HTTPStatus.NO_CONTENT)


class PurgeRequestModel(LegacyBaseRequestModel):
    vfolder_id: uuid.UUID = Field(
        validation_alias=AliasChoices("id", "vfolderId"),
        description="Target vfolder id to purge, permanently remove from DB",
    )


@auth_required
@server_status_required(ALL_ALLOWED)
@pydantic_params_api_handler(PurgeRequestModel)
async def purge(request: web.Request, params: PurgeRequestModel) -> web.Response:
    """
    Delete `delete-complete`d vfolder rows in DB
    """
    root_ctx: RootContext = request.app["_root.context"]
    folder_id = params.vfolder_id
    log.info(
        "VFOLDER.PURGE (email:{}, ak:{}, vf:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
        folder_id,
    )
    if request["user"]["role"] not in (
        UserRole.ADMIN,
        UserRole.SUPERADMIN,
    ):
        raise InsufficientPrivilege("You are not allowed to purge vfolders")

    async with root_ctx.db.begin_session() as db_session:
        row = await db_session.scalar(sa.select(VFolderDBRow).where(VFolderDBRow.id == folder_id))
        row = cast(VFolderDBRow | None, row)
        if row is None:
            raise VFolderNotFound(extra_data=folder_id)
        await check_vfolder_status({"status": row.status}, VFolderStatusSet.PURGABLE)
        delete_stmt = sa.delete(VFolderDBRow).where(VFolderDBRow.id == folder_id)
        await db_session.execute(delete_stmt)

    return web.Response(status=HTTPStatus.NO_CONTENT)


class RestoreRequestModel(LegacyBaseRequestModel):
    vfolder_id: uuid.UUID = Field(
        validation_alias=AliasChoices("id", "vfolderId"),
        description="Target vfolder id to restore",
    )


@auth_required
@server_status_required(ALL_ALLOWED)
@pydantic_params_api_handler(RestoreRequestModel)
async def restore(request: web.Request, params: RestoreRequestModel) -> web.Response:
    """
    Recover vfolder from trash bin, by changing status.
    """
    root_ctx: RootContext = request.app["_root.context"]
    folder_id = params.vfolder_id
    user_uuid = request["user"]["uuid"]
    log.info(
        "VFOLDER.RESTORE (email: {}, ak:{}, vf:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
        folder_id,
    )

    await root_ctx.processors.vfolder.restore_vfolder_from_trash.wait_for_complete(
        RestoreVFolderFromTrashAction(
            user_uuid=user_uuid,
            vfolder_uuid=folder_id,
        )
    )
    return web.Response(status=HTTPStatus.NO_CONTENT)


@auth_required
@server_status_required(ALL_ALLOWED)
@with_vfolder_rows_resolved(VFolderPermissionSetAlias.READABLE, allow_privileged_access=False)
@with_vfolder_status_checked(VFolderStatusSet.UPDATABLE)
@check_api_params(
    t.Dict({
        tx.AliasedKey(["shared_user_uuid", "sharedUserUuid"], default=None): t.String | t.Null,
    }),
)
async def leave(request: web.Request, params: Any, row: VFolderRow) -> web.Response:
    """
    Leave from shared VFolder.

    Cannot leave a group VFolder or a VFolder that the requesting user owns.
    """

    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    rqst_user_uuid = request["user"]["uuid"]
    vfolder_id = row["id"]
    perm = row["permission"]

    log.info(
        "VFOLDER.LEAVE(email:{}, ak:{}, vf:{} (resolved-from:{!r}), uid:{}, perm:{})",
        request["user"]["email"],
        access_key,
        vfolder_id,
        request.match_info["name"],
        rqst_user_uuid,
        perm,
    )
    if row["ownership_type"] == VFolderOwnershipType.GROUP:
        raise InvalidAPIParameters("Cannot leave a group vfolder.")
    await root_ctx.processors.vfolder_invite.leave_invited_vfolder.wait_for_complete(
        LeaveInvitedVFolderAction(
            vfolder_uuid=vfolder_id,
            requester_user_uuid=rqst_user_uuid,
            shared_user_uuid=params["shared_user_uuid"],
        )
    )
    resp = {"msg": "left the shared vfolder"}
    return web.json_response(resp, status=HTTPStatus.OK)


@auth_required
@server_status_required(ALL_ALLOWED)
@with_vfolder_rows_resolved(VFolderPermissionSetAlias.READABLE)
@with_vfolder_status_checked(VFolderStatusSet.UPDATABLE)
@check_api_params(
    t.Dict({
        t.Key("cloneable", default=False): t.Bool,
        t.Key("target_name"): tx.Slug(allow_dot=True),
        t.Key("target_host", default=None) >> "folder_host": t.String | t.Null,
        t.Key("usage_mode", default="general"): tx.Enum(VFolderUsageMode) | t.Null,
        t.Key("permission", default="rw"): tx.Enum(VFolderPermission) | t.Null,
    }),
)
async def clone(request: web.Request, params: Any, row: VFolderRow) -> web.Response:
    resp: Dict[str, Any] = {}
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    user_uuid = request["user"]["uuid"]
    log.info(
        "VFOLDER.CLONE (email:{}, ak:{}, vf:{} (resolved-from:{!r}), vft:{}, vfh:{}, umod:{}, perm:{})",
        request["user"]["email"],
        access_key,
        row["id"],
        request.match_info["name"],
        params["target_name"],
        params["folder_host"],
        params["usage_mode"].value,
        params["permission"].value,
    )

    result = await root_ctx.processors.vfolder.clone_vfolder.wait_for_complete(
        CloneVFolderAction(
            requester_user_uuid=user_uuid,
            source_vfolder_uuid=row["id"],
            target_name=params["target_name"],
            target_host=params["folder_host"],
            cloneable=params["cloneable"],
            usage_mode=params["usage_mode"],
            mount_permission=params["permission"],
        )
    )
    resp = {
        "id": result.target_vfolder_id.hex,
        "name": params["target_name"],
        "host": result.target_vfolder_host,
        "usage_mode": result.usage_mode.value,
        "permission": result.mount_permission.value,
        "creator": request["user"]["email"],
        "ownership_type": result.ownership_type.value,
        "user": str(result.owner_user_uuid) if result.owner_user_uuid is not None else None,
        "group": str(result.owner_group_uuid) if result.owner_group_uuid is not None else None,
        "cloneable": params["cloneable"],
        "bgtask_id": str(result.bgtask_id),
    }
    return web.json_response(resp, status=HTTPStatus.CREATED)


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict({
        tx.AliasedKey(["vfolder_id", "vfolderId"], default=None): tx.UUID | t.Null,
    }),
)
async def list_shared_vfolders(request: web.Request, params: Any) -> web.Response:
    """
    List shared vfolders.

    Not available for group vfolders.
    """
    root_ctx: RootContext = request.app["_root.context"]
    target_vfid = params["vfolder_id"]
    log.info(
        "VFOLDER.LIST_SHARED_VFOLDERS (email:{}, ak:{}, vf:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
        target_vfid,
    )
    async with root_ctx.db.begin() as conn:
        j = vfolder_permissions.join(vfolders, vfolders.c.id == vfolder_permissions.c.vfolder).join(
            users, users.c.uuid == vfolder_permissions.c.user
        )
        query = sa.select([
            vfolder_permissions,
            vfolders.c.id.label("vfolder_id"),
            vfolders.c.name,
            vfolders.c.group,
            vfolders.c.status,
            vfolders.c.user.label("vfolder_user"),
            users.c.email,
        ]).select_from(j)
        if target_vfid is not None:
            query = query.where(vfolders.c.id == target_vfid)
        result = await conn.execute(query)
        shared_list = result.fetchall()
    shared_info = []
    for shared in shared_list:
        owner = shared.group if shared.group else shared.vfolder_user
        folder_type = "project" if shared.group else "user"
        shared_info.append({
            "vfolder_id": str(shared.vfolder_id),
            "vfolder_name": str(shared.name),
            "status": shared.status.value,
            "owner": str(owner),
            "type": folder_type,
            "shared_to": {
                "uuid": str(shared.user),
                "email": shared.email,
            },
            "perm": shared.permission.value,
        })
    resp = {"shared": shared_info}
    return web.json_response(resp, status=HTTPStatus.OK)


@auth_required
@server_status_required(ALL_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key("vfolder"): tx.UUID,
        t.Key("user"): tx.UUID,
        tx.AliasedKey(["perm", "permission"]): VFolderPermissionValidator | t.Null,
    }),
)
async def update_shared_vfolder(request: web.Request, params: Any) -> web.Response:
    """
    Update permission for shared vfolders.

    If params['perm'] is None, remove user's permission for the vfolder.
    """
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    vfolder_id = params["vfolder"]
    user_uuid = params["user"]
    perm = params["perm"]
    log.info(
        "VFOLDER.UPDATE_SHARED_VFOLDER(email:{}, ak:{}, vf:{}, uid:{}, perm:{})",
        request["user"]["email"],
        access_key,
        vfolder_id,
        user_uuid,
        perm,
    )
    if perm is not None:
        await root_ctx.processors.vfolder_invite.update_invited_vfolder_mount_permission.wait_for_complete(
            UpdateInvitedVFolderMountPermissionAction(
                vfolder_id=vfolder_id,
                user_id=user_uuid,
                permission=perm,
            )
        )
    else:
        await root_ctx.processors.vfolder_invite.revoke_invited_vfolder.wait_for_complete(
            RevokeInvitedVFolderAction(vfolder_id=vfolder_id, shared_user_id=user_uuid)
        )
    resp = {"msg": "shared vfolder permission updated"}
    return web.json_response(resp, status=HTTPStatus.OK)


class UserPermMapping(BaseFieldModel):
    user_id: uuid.UUID = Field(
        description="Target user id to update sharing status.",
        validation_alias=AliasChoices("user", "userID"),
    )
    perm: VFolderPermission | None = Field(
        default=None,
        description=textwrap.dedent(
            "Permission to update. Delete the sharing between vfolder and user if this value is null. "
            f"Should be one of {[p.value for p in VFolderPermission]}. "
            "Default value is null."
        ),
        alias="permission",
    )


class UpdateSharedRequestModel(LegacyBaseRequestModel):
    vfolder_id: uuid.UUID = Field(
        description="Target vfolder id to update sharing status.",
        alias="vfolder",
    )
    user_perm_list: list[UserPermMapping] = Field(
        description="A list of user and permission mappings.",
        validation_alias=AliasChoices("user_perm", "userPermList"),
    )


@auth_required
@server_status_required(ALL_ALLOWED)
@pydantic_params_api_handler(UpdateSharedRequestModel)
async def update_vfolder_sharing_status(
    request: web.Request, params: UpdateSharedRequestModel
) -> web.Response:
    """
    Update permission for shared vfolders.
    """
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    vfolder_id = params.vfolder_id
    user_perm_list = params.user_perm_list
    log.info(
        "VFOLDER.UPDATE_VFOLDER_SHARING_STATUS(email:{}, ak:{}, vf:{}, data:{})",
        request["user"]["email"],
        access_key,
        vfolder_id,
        user_perm_list,
    )

    to_delete: list[uuid.UUID] = []
    to_update: list[Mapping[str, Any]] = []
    for mapping in user_perm_list:
        if mapping.perm is None:
            to_delete.append(mapping.user_id)
        else:
            to_update.append({
                "user_id": mapping.user_id,
                "perm": mapping.perm,
            })

    async def _update_or_delete(db_session: SASession) -> None:
        if to_delete:
            stmt = (
                sa.delete(VFolderPermissionRow)
                .where(VFolderPermissionRow.vfolder == vfolder_id)
                .where(VFolderPermissionRow.user.in_(to_delete))
            )
            await db_session.execute(stmt)

        if to_update:
            stmt = (
                sa.update(VFolderPermissionRow)
                .values(permission=sa.bindparam("perm"))
                .where(VFolderPermissionRow.vfolder == vfolder_id)
                .where(VFolderPermissionRow.user == sa.bindparam("user_id"))
            )
            await db_session.execute(stmt, to_update)

    async with root_ctx.db.connect() as db_conn:
        await execute_with_txn_retry(_update_or_delete, root_ctx.db.begin_session, db_conn)
    return web.Response(status=HTTPStatus.CREATED)


@superadmin_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key("fstab_path", default=None): t.String | t.Null,
        t.Key("agent_id", default=None): t.String | t.Null,
    }),
)
async def get_fstab_contents(request: web.Request, params: Any) -> web.Response:
    """
    Return the contents of `/etc/fstab` file.
    """
    access_key = request["keypair"]["access_key"]
    log.info(
        "VFOLDER.GET_FSTAB_CONTENTS(email:{}, ak:{}, ag:{})",
        request["user"]["email"],
        access_key,
        params["agent_id"],
    )
    if params["fstab_path"] is None:
        params["fstab_path"] = "/etc/fstab"
    if params["agent_id"] is not None:
        # Return specific agent's fstab.
        watcher_info = await get_watcher_info(request, params["agent_id"])
        try:
            client_timeout = aiohttp.ClientTimeout(total=10.0)
            async with aiohttp.ClientSession(timeout=client_timeout) as sess:
                headers = {"X-BackendAI-Watcher-Token": watcher_info["token"]}
                url = watcher_info["addr"] / "fstab"
                async with sess.get(url, headers=headers, params=params) as watcher_resp:
                    if watcher_resp.status == 200:
                        content = await watcher_resp.text()
                        resp = {
                            "content": content,
                            "node": "agent",
                            "node_id": params["agent_id"],
                        }
                        return web.json_response(resp)
                    else:
                        message = await watcher_resp.text()
                        raise BackendAgentError(
                            "FAILURE", f"({watcher_resp.status}: {watcher_resp.reason}) {message}"
                        )
        except asyncio.CancelledError:
            raise
        except asyncio.TimeoutError:
            log.error(
                "VFOLDER.GET_FSTAB_CONTENTS(u:{}): timeout from watcher (agent:{})",
                access_key,
                params["agent_id"],
            )
            raise BackendAgentError("TIMEOUT", "Could not fetch fstab data from agent")
        except Exception:
            log.exception(
                "VFOLDER.GET_FSTAB_CONTENTS(u:{}): "
                "unexpected error while reading from watcher (agent:{})",
                access_key,
                params["agent_id"],
            )
            raise InternalServerError
    else:
        resp = {
            "content": (
                "# Since Backend.AI 20.09, reading the manager fstab is no longer supported."
            ),
            "node": "manager",
            "node_id": "manager",
        }
        return web.json_response(resp)


@superadmin_required
@server_status_required(READ_ALLOWED)
async def list_mounts(request: web.Request) -> web.Response:
    """
    List all mounted vfolder hosts in vfroot.

    All mounted hosts from connected (ALIVE) agents are also gathered.
    Generally, agents should be configured to have same hosts structure,
    but newly introduced one may not.
    """
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    log.info(
        "VFOLDER.LIST_MOUNTS(ak:{})",
        access_key,
    )
    mount_prefix = await root_ctx.config_provider.legacy_etcd_config_loader.get_raw(
        "volumes/_mount"
    )
    if mount_prefix is None:
        mount_prefix = "/mnt"

    # NOTE: Changed in 20.09: the manager instances no longer have mountpoints.
    all_volumes = [*await root_ctx.storage_manager.get_all_volumes()]
    all_mounts = [volume_data["path"] for proxy_name, volume_data in all_volumes]
    all_vfolder_hosts = [
        f"{proxy_name}:{volume_data['name']}" for proxy_name, volume_data in all_volumes
    ]
    resp: MutableMapping[str, Any] = {
        "manager": {
            "success": True,
            "mounts": all_mounts,
            "message": "(legacy)",
        },
        "storage-proxy": {
            "success": True,
            "mounts": [*zip(all_vfolder_hosts, all_mounts)],
            "message": "",
        },
        "agents": {},
    }

    # Scan mounted vfolder hosts for connected agents.
    async def _fetch_mounts(
        sema: asyncio.Semaphore,
        sess: aiohttp.ClientSession,
        agent_id: str,
    ) -> Tuple[str, Mapping]:
        async with sema:
            watcher_info = await get_watcher_info(request, agent_id)
            headers = {"X-BackendAI-Watcher-Token": watcher_info["token"]}
            url = watcher_info["addr"] / "mounts"
            try:
                async with sess.get(url, headers=headers) as watcher_resp:
                    if watcher_resp.status == 200:
                        data = {
                            "success": True,
                            "mounts": await watcher_resp.json(),
                            "message": "",
                        }
                    else:
                        data = {
                            "success": False,
                            "mounts": [],
                            "message": await watcher_resp.text(),
                        }
                    return (agent_id, data)
            except asyncio.CancelledError:
                raise
            except asyncio.TimeoutError:
                log.error(
                    "VFOLDER.LIST_MOUNTS(u:{}): timeout from watcher (agent:{})",
                    access_key,
                    agent_id,
                )
                raise
            except Exception:
                log.exception(
                    "VFOLDER.LIST_MOUNTS(u:{}): "
                    "unexpected error while reading from watcher (agent:{})",
                    access_key,
                    agent_id,
                )
                raise

    async with root_ctx.db.begin() as conn:
        query = (
            sa.select([agents.c.id]).select_from(agents).where(agents.c.status == AgentStatus.ALIVE)
        )
        result = await conn.execute(query)
        rows = result.fetchall()

    client_timeout = aiohttp.ClientTimeout(total=10.0)
    async with aiohttp.ClientSession(timeout=client_timeout) as sess:
        sema = asyncio.Semaphore(8)
        mounts = await asyncio.gather(
            *[_fetch_mounts(sema, sess, row.id) for row in rows], return_exceptions=True
        )
        for mount in mounts:
            match mount:
                case BaseException():
                    continue
                case _:
                    resp["agents"][mount[0]] = mount[1]

    return web.json_response(resp, status=HTTPStatus.OK)


@superadmin_required
@server_status_required(ALL_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key("fs_location"): t.String,
        t.Key("name"): t.String,
        t.Key("fs_type", default="nfs"): t.String,
        t.Key("options", default=None): t.String | t.Null,
        t.Key("scaling_group", default=None): t.String | t.Null,
        t.Key("fstab_path", default=None): t.String | t.Null,
        t.Key("edit_fstab", default=False): t.ToBool,
    }),
)
async def mount_host(request: web.Request, params: Any) -> web.Response:
    """
    Mount device into vfolder host.

    Mount a device (eg: nfs) located at `fs_location` into `<vfroot>/name` in the
    host machines (manager and all agents). `fs_type` can be specified by requester,
    which fallbaks to 'nfs'.

    If `scaling_group` is specified, try to mount for agents in the scaling group.
    """
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    log_fmt = "VFOLDER.MOUNT_HOST(ak:{}, name:{}, fs:{}, sg:{})"
    log_args = (access_key, params["name"], params["fs_location"], params["scaling_group"])
    log.info(log_fmt, *log_args)
    mount_prefix = await root_ctx.config_provider.legacy_etcd_config_loader.get_raw(
        "volumes/_mount"
    )
    if mount_prefix is None:
        mount_prefix = "/mnt"

    # NOTE: Changed in 20.09: the manager instances no longer have mountpoints.
    resp: MutableMapping[str, Any] = {
        "manager": {
            "success": True,
            "message": "Managers do not have mountpoints since v20.09.",
        },
        "agents": {},
    }

    # Mount on running agents.
    async with root_ctx.db.begin() as conn:
        query = (
            sa.select([agents.c.id]).select_from(agents).where(agents.c.status == AgentStatus.ALIVE)
        )
        if params["scaling_group"] is not None:
            query = query.where(agents.c.scaling == params["scaling_group"])
        result = await conn.execute(query)
        rows = result.fetchall()

    async def _mount(
        sema: asyncio.Semaphore,
        sess: aiohttp.ClientSession,
        agent_id: str,
    ) -> Tuple[str, Mapping]:
        async with sema:
            watcher_info = await get_watcher_info(request, agent_id)
            try:
                headers = {"X-BackendAI-Watcher-Token": watcher_info["token"]}
                url = watcher_info["addr"] / "mounts"
                async with sess.post(url, json=params, headers=headers) as resp:
                    if resp.status == 200:
                        data = {
                            "success": True,
                            "message": await resp.text(),
                        }
                    else:
                        data = {
                            "success": False,
                            "message": await resp.text(),
                        }
                    return (agent_id, data)
            except asyncio.CancelledError:
                raise
            except asyncio.TimeoutError:
                log.error(
                    log_fmt + ": timeout from watcher (ag:{})",
                    *log_args,
                    agent_id,
                )
                raise
            except Exception:
                log.exception(
                    log_fmt + ": unexpected error while reading from watcher (ag:{})",
                    *log_args,
                    agent_id,
                )
                raise

    client_timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=client_timeout) as sess:
        sema = asyncio.Semaphore(8)
        results = await asyncio.gather(
            *[_mount(sema, sess, row.id) for row in rows], return_exceptions=True
        )
        for result in results:
            if isinstance(result, BaseException):
                # exceptions are already logged.
                continue
            resp["agents"][result[0]] = result[1]

    return web.json_response(resp, status=HTTPStatus.OK)


@superadmin_required
@server_status_required(ALL_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key("name"): t.String,
        t.Key("scaling_group", default=None): t.String | t.Null,
        t.Key("fstab_path", default=None): t.String | t.Null,
        t.Key("edit_fstab", default=False): t.ToBool,
    }),
)
async def umount_host(request: web.Request, params: Any) -> web.Response:
    """
    Unmount device from vfolder host.

    Unmount a device (eg: nfs) located at `<vfroot>/name` from the host machines
    (manager and all agents).

    If `scaling_group` is specified, try to unmount for agents in the scaling group.
    """
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    log_fmt = "VFOLDER.UMOUNT_HOST(ak:{}, name:{}, sg:{})"
    log_args = (access_key, params["name"], params["scaling_group"])
    log.info(log_fmt, *log_args)
    mount_prefix = await root_ctx.config_provider.legacy_etcd_config_loader.get_raw(
        "volumes/_mount"
    )
    if mount_prefix is None:
        mount_prefix = "/mnt"
    mountpoint = Path(mount_prefix) / params["name"]
    assert Path(mount_prefix) != mountpoint

    async with root_ctx.db.begin() as conn, conn.begin():
        # Prevent unmount if target host is mounted to running kernels.
        query = (
            sa.select([kernels.c.mounts])
            .select_from(kernels)
            .where(kernels.c.status != KernelStatus.TERMINATED)
        )
        result = await conn.execute(query)
        _kernels = result.fetchall()
        _mounted = set()
        for kern in _kernels:
            if kern.mounts:
                _mounted.update([m[1] for m in kern.mounts])
        if params["name"] in _mounted:
            return web.json_response(
                {
                    "title": "Target host is used in sessions",
                    "message": "Target host is used in sessions",
                },
                status=HTTPStatus.CONFLICT,
            )

        query = (
            sa.select([agents.c.id]).select_from(agents).where(agents.c.status == AgentStatus.ALIVE)
        )
        if params["scaling_group"] is not None:
            query = query.where(agents.c.scaling == params["scaling_group"])
        result = await conn.execute(query)
        _agents = result.fetchall()

    # Unmount from manager.
    # NOTE: Changed in 20.09: the manager instances no longer have mountpoints.
    resp: MutableMapping[str, Any] = {
        "manager": {
            "success": True,
            "message": "Managers do not have mountpoints since v20.09.",
        },
        "agents": {},
    }

    # Unmount from running agents.
    async def _umount(
        sema: asyncio.Semaphore,
        sess: aiohttp.ClientSession,
        agent_id: str,
    ) -> Tuple[str, Mapping]:
        async with sema:
            watcher_info = await get_watcher_info(request, agent_id)
            try:
                headers = {"X-BackendAI-Watcher-Token": watcher_info["token"]}
                url = watcher_info["addr"] / "mounts"
                async with sess.delete(url, json=params, headers=headers) as resp:
                    if resp.status == 200:
                        data = {
                            "success": True,
                            "message": await resp.text(),
                        }
                    else:
                        data = {
                            "success": False,
                            "message": await resp.text(),
                        }
                    return (agent_id, data)
            except asyncio.CancelledError:
                raise
            except asyncio.TimeoutError:
                log.error(
                    log_fmt + ": timeout from watcher (agent:{})",
                    *log_args,
                    agent_id,
                )
                raise
            except Exception:
                log.exception(
                    log_fmt + ": unexpected error while reading from watcher (agent:{})",
                    *log_args,
                    agent_id,
                )
                raise

    client_timeout = aiohttp.ClientTimeout(total=10.0)
    async with aiohttp.ClientSession(timeout=client_timeout) as sess:
        sema = asyncio.Semaphore(8)
        results = await asyncio.gather(
            *[_umount(sema, sess, _agent.id) for _agent in _agents], return_exceptions=True
        )
        for result in results:
            if isinstance(result, BaseException):
                # exceptions are already logged.
                continue
            resp["agents"][result[0]] = result[1]

    return web.json_response(resp, status=HTTPStatus.OK)


async def storage_task_exception_handler(
    exc_type: type[BaseException],
    exc_obj: BaseException,
    exc_tb: TracebackType,
) -> None:
    log.exception("Error while removing vFolder", exc_info=exc_obj)


@superadmin_required
@server_status_required(ALL_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key("vfolder"): tx.UUID,
        t.Key("user_email"): t.String,
    }),
)
async def change_vfolder_ownership(request: web.Request, params: Any) -> web.Response:
    """
    Change the ownership of vfolder
    For now, we only provide changing the ownership of user-folder
    """
    vfolder_id = params["vfolder"]
    user_email = params["user_email"]
    root_ctx: RootContext = request.app["_root.context"]

    allowed_hosts_by_user = VFolderHostPermissionMap()
    async with root_ctx.db.begin_readonly() as conn:
        j = sa.join(users, keypairs, users.c.email == keypairs.c.user_id)
        query = (
            sa.select([users.c.uuid, users.c.domain_name, keypairs.c.resource_policy])
            .select_from(j)
            .where((users.c.email == user_email) & (users.c.status == UserStatus.ACTIVE))
        )
        try:
            result = await conn.execute(query)
        except sa.exc.DataError:
            raise InvalidAPIParameters
        user_info = result.first()
        if user_info is None:
            raise ObjectNotFound(object_name="user")
        resource_policy_name = user_info.resource_policy
        result = await conn.execute(
            sa.select([keypair_resource_policies.c.allowed_vfolder_hosts]).where(
                keypair_resource_policies.c.name == resource_policy_name
            )
        )
        resource_policy = result.first()
        allowed_hosts_by_user = await get_allowed_vfolder_hosts_by_user(
            conn=conn,
            resource_policy=resource_policy,
            domain_name=user_info.domain_name,
            user_uuid=user_info.uuid,
        )
    log.info(
        "VFOLDER.CHANGE_VFOLDER_OWNERSHIP(email:{}, ak:{}, vfid:{}, uid:{})",
        request["user"]["email"],
        request["keypair"]["access_key"],
        vfolder_id,
        user_info.uuid,
    )
    async with root_ctx.db.begin_readonly() as conn:
        query = (
            sa.select([vfolders.c.host])
            .select_from(vfolders)
            .where(
                (vfolders.c.id == vfolder_id)
                & (vfolders.c.ownership_type == VFolderOwnershipType.USER)
            )
        )
        folder_host = await conn.scalar(query)
    if folder_host not in allowed_hosts_by_user:
        raise VFolderOperationFailed("User to migrate vfolder needs an access to the storage host.")

    async def _update() -> None:
        async with root_ctx.db.begin() as conn:
            # TODO: we need to implement migration from project to other project
            #       for now we only support migration btw user folder only
            # TODO: implement quota-scope migration and progress checks
            query = (
                sa.update(vfolders)
                .values(user=user_info.uuid)
                .where(
                    (vfolders.c.id == vfolder_id)
                    & (vfolders.c.ownership_type == VFolderOwnershipType.USER)
                )
            )
            await conn.execute(query)

    await execute_with_retry(_update)

    async def _delete_vfolder_related_rows() -> None:
        async with root_ctx.db.begin() as conn:
            # delete vfolder_invitation if the new owner user has already been shared with the vfolder
            query = sa.delete(vfolder_invitations).where(
                (vfolder_invitations.c.invitee == user_email)
                & (vfolder_invitations.c.vfolder == vfolder_id)
            )
            await conn.execute(query)
            # delete vfolder_permission if the new owner user has already been shared with the vfolder
            query = sa.delete(vfolder_permissions).where(
                (vfolder_permissions.c.vfolder == vfolder_id)
                & (vfolder_permissions.c.user == user_info.uuid)
            )
            await conn.execute(query)

    await execute_with_retry(_delete_vfolder_related_rows)

    return web.json_response({}, status=HTTPStatus.OK)


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    database_ptask_group: aiotools.PersistentTaskGroup
    storage_ptask_group: aiotools.PersistentTaskGroup


async def init(app: web.Application) -> None:
    app_ctx: PrivateContext = app["folders.context"]
    app_ctx.database_ptask_group = aiotools.PersistentTaskGroup()
    app_ctx.storage_ptask_group = aiotools.PersistentTaskGroup(
        exception_handler=storage_task_exception_handler
    )


async def shutdown(app: web.Application) -> None:
    app_ctx: PrivateContext = app["folders.context"]
    await app_ctx.database_ptask_group.shutdown()
    await app_ctx.storage_ptask_group.shutdown()


def create_app(default_cors_options):
    app = web.Application()
    app["prefix"] = "folders"
    app["api_versions"] = (2, 3, 4)
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    app["folders.context"] = PrivateContext()
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route
    root_resource = cors.add(app.router.add_resource(r""))
    cors.add(root_resource.add_route("POST", create))
    cors.add(root_resource.add_route("GET", list_folders))
    cors.add(root_resource.add_route("DELETE", delete_by_id))
    vfolder_resource = cors.add(app.router.add_resource(r"/{name}"))
    cors.add(vfolder_resource.add_route("GET", get_info))
    cors.add(vfolder_resource.add_route("DELETE", delete_by_name))
    cors.add(add_route("GET", r"/_/id", get_vfolder_id))
    cors.add(add_route("GET", r"/_/hosts", list_hosts))
    cors.add(add_route("GET", r"/_/all-hosts", list_all_hosts))
    cors.add(add_route("GET", r"/_/allowed-types", list_allowed_types))
    cors.add(add_route("GET", r"/_/all_hosts", list_all_hosts))  # legacy underbar
    cors.add(add_route("GET", r"/_/allowed_types", list_allowed_types))  # legacy underbar
    cors.add(add_route("GET", r"/_/perf-metric", get_volume_perf_metric))
    cors.add(add_route("POST", r"/{name}/rename", rename_vfolder))
    cors.add(add_route("POST", r"/{name}/update-options", update_vfolder_options))
    cors.add(add_route("POST", r"/{name}/mkdir", mkdir))
    cors.add(add_route("POST", r"/{name}/request-upload", create_upload_session))
    cors.add(add_route("POST", r"/{name}/request-download", create_download_session))
    cors.add(add_route("POST", r"/{name}/move-file", move_file))
    cors.add(add_route("POST", r"/{name}/rename-file", rename_file))
    cors.add(add_route("POST", r"/{name}/delete-files", delete_files))
    cors.add(add_route("DELETE", r"/{name}/delete-files", delete_files))
    cors.add(add_route("POST", r"/{name}/rename_file", rename_file))  # legacy underbar
    cors.add(add_route("DELETE", r"/{name}/delete_files", delete_files))  # legacy underbar
    cors.add(add_route("GET", r"/{name}/files", list_files))
    cors.add(add_route("POST", r"/{name}/invite", invite))
    cors.add(add_route("POST", r"/{name}/leave", leave))
    cors.add(add_route("POST", r"/{name}/share", share))
    cors.add(add_route("POST", r"/{name}/unshare", unshare))
    cors.add(add_route("DELETE", r"/{name}/unshare", unshare))
    cors.add(add_route("POST", r"/{name}/clone", clone))
    cors.add(add_route("POST", r"/purge", purge))
    cors.add(add_route("POST", r"/restore-from-trash-bin", restore))
    cors.add(add_route("POST", r"/delete-from-trash-bin", delete_from_trash_bin))
    cors.add(add_route("DELETE", r"/{folder_id}/force", force_delete))
    cors.add(add_route("GET", r"/invitations/list-sent", list_sent_invitations))
    cors.add(add_route("GET", r"/invitations/list_sent", list_sent_invitations))  # legacy underbar
    cors.add(add_route("POST", r"/invitations/update/{inv_id}", update_invitation))
    cors.add(add_route("GET", r"/invitations/list", invitations))
    cors.add(add_route("POST", r"/invitations/accept", accept_invitation))
    cors.add(add_route("POST", r"/invitations/delete", delete_invitation))
    cors.add(add_route("DELETE", r"/invitations/delete", delete_invitation))
    cors.add(add_route("GET", r"/_/shared", list_shared_vfolders))
    cors.add(add_route("POST", r"/_/shared", update_shared_vfolder))
    cors.add(add_route("POST", r"/_/sharing", update_vfolder_sharing_status))
    cors.add(add_route("GET", r"/_/fstab", get_fstab_contents))
    cors.add(add_route("GET", r"/_/mounts", list_mounts))
    cors.add(add_route("POST", r"/_/mounts", mount_host))
    cors.add(add_route("POST", r"/_/umounts", umount_host))
    cors.add(add_route("DELETE", r"/_/mounts", umount_host))
    cors.add(add_route("POST", r"/_/change-ownership", change_vfolder_ownership))
    cors.add(add_route("GET", r"/_/quota", get_quota))
    cors.add(add_route("POST", r"/_/quota", update_quota))
    cors.add(add_route("GET", r"/_/usage", get_usage))
    cors.add(add_route("GET", r"/_/used-bytes", get_used_bytes))
    return app, []
