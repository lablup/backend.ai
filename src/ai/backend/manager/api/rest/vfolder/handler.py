"""VFolder handler class using the ApiHandler pattern.

All handlers use typed parameters (``BodyParam``, ``QueryParam``,
``UserContext``, ``RequestCtx``, ``VFolderAuthContext``, ``ProcessorsCtx``)
that are automatically extracted by ``_wrap_api_handler``, and responses are
returned as ``APIResponse`` objects.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Mapping
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, cast

import aiohttp
import sqlalchemy as sa

from ai.backend.common.api_handlers import APIResponse, BodyParam, QueryParam
from ai.backend.common.dto.manager.field import (
    VFolderItemField,
    VFolderOperationStatusField,
    VFolderOwnershipTypeField,
    VFolderPermissionField,
)
from ai.backend.common.dto.manager.vfolder.request import (
    AcceptInvitationReq,
    ChangeVFolderOwnershipReq,
    CloneVFolderReq,
    CreateDownloadSessionReq,
    CreateUploadSessionReq,
    DeleteFilesAsyncBodyParam,
    DeleteFilesReq,
    DeleteInvitationReq,
    DeleteVFolderByIDReq,
    DeleteVFolderFromTrashReq,
    GetFstabContentsQuery,
    GetQuotaQuery,
    GetUsageQuery,
    GetUsedBytesQuery,
    GetVFolderIDReq,
    GetVolumePerfMetricQuery,
    InviteVFolderReq,
    LeaveVFolderReq,
    ListFilesQuery,
    ListHostsQuery,
    ListSharedVFoldersQuery,
    ListVFoldersQuery,
    MkdirReq,
    MountHostReq,
    MoveFileReq,
    PurgeVFolderReq,
    RenameFileReq,
    RenameVFolderReq,
    RestoreVFolderReq,
    ShareVFolderReq,
    UmountHostReq,
    UnshareVFolderReq,
    UpdateInvitationReq,
    UpdateQuotaReq,
    UpdateSharedVFolderReq,
    UpdateVFolderOptionsReq,
    UpdateVFolderSharingStatusReq,
    VFolderCreateReq,
)
from ai.backend.common.dto.manager.vfolder.response import (
    CompactVFolderInfoDTO,
    CreateDownloadSessionResponse,
    CreateUploadSessionResponse,
    DeleteFilesAsyncResponse,
    GetFstabContentsResponse,
    GetQuotaResponse,
    GetUsageResponse,
    GetUsedBytesResponse,
    GetVolumePerfMetricResponse,
    InviteVFolderResponse,
    ListAllHostsResponse,
    ListAllowedTypesResponse,
    ListFilesResponse,
    ListHostsResponse,
    ListInvitationsResponse,
    ListMountsResponse,
    ListSentInvitationsResponse,
    ListSharedVFoldersResponse,
    MessageResponse,
    MkdirResponse,
    MountResultDTO,
    ShareVFolderResponse,
    UnshareVFolderResponse,
    UpdateQuotaResponse,
    VFolderCloneInfoDTO,
    VFolderCloneResponse,
    VFolderCreateResponse,
    VFolderGetIDResponse,
    VFolderGetInfoResponse,
    VFolderInfoDTO,
    VFolderInvitationDTO,
    VFolderListResponse,
    VFolderSharedInfoDTO,
    VolumeInfoDTO,
)
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import (
    VFolderHostPermission,
    VFolderID,
    VFolderUsageMode,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.resource import get_watcher_info
from ai.backend.manager.api.utils import get_user_scopes
from ai.backend.manager.api.vfolder import (
    check_vfolder_status,
    resolve_vfolder_rows,
)
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.data.permission.types import ScopeType
from ai.backend.manager.dto.context import (
    ProcessorsCtx,
    RequestCtx,
    UserContext,
    VFolderAuthContext,
)
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.errors.kernel import BackendAgentError
from ai.backend.manager.errors.service import ModelServiceDependencyNotCleared
from ai.backend.manager.errors.storage import (
    TooManyVFoldersFound,
    VFolderAlreadyExists,
    VFolderBadRequest,
    VFolderInvalidParameter,
    VFolderOperationFailed,
)
from ai.backend.manager.models.agent import agents
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.kernel import kernels
from ai.backend.manager.models.user import (
    UserRole,
)
from ai.backend.manager.models.vfolder import (
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
    VFolderPermissionSetAlias,
    VFolderRow,
    VFolderStatusSet,
    delete_vfolder_relation_rows,
    ensure_host_permission_allowed,
    update_vfolder_status,
)
from ai.backend.manager.repositories.base.rbac.entity_purger import RBACEntityPurger
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.vfolder.purgers import VFolderPurgerSpec
from ai.backend.manager.repositories.vfolder.updaters import VFolderAttributeUpdaterSpec
from ai.backend.manager.services.vfolder.actions.base import (
    CloneVFolderAction,
    CreateVFolderAction,
    DeleteForeverVFolderAction,
    ForceDeleteVFolderAction,
    GetVFolderAction,
    ListVFolderAction,
    MoveToTrashVFolderAction,
    PurgeVFolderAction,
    RestoreVFolderFromTrashAction,
    UpdateVFolderAttributeAction,
)
from ai.backend.manager.services.vfolder.actions.file import (
    CreateArchiveDownloadSessionAction,
    CreateDownloadSessionAction,
    CreateUploadSessionAction,
    DeleteFilesAction,
    DeleteFilesAsyncAction,
    ListFilesAction,
    MkdirAction,
    MoveFileAction,
    RenameFileAction,
)
from ai.backend.manager.services.vfolder.actions.invite import (
    AcceptInvitationAction,
    InviteVFolderAction,
    LeaveInvitedVFolderAction,
    ListInvitationAction,
    ListSentInvitationsAction,
    RejectInvitationAction,
    RevokeInvitedVFolderAction,
    UpdateInvitationAction,
    UpdateInvitedVFolderMountPermissionAction,
)
from ai.backend.manager.services.vfolder.actions.sharing import (
    ListSharedVFoldersAction,
    ShareVFolderAction,
    UnshareVFolderAction,
    UpdateVFolderSharingStatusAction,
)
from ai.backend.manager.services.vfolder.actions.storage_ops import (
    ChangeVFolderOwnershipAction,
    GetQuotaAction,
    GetVFolderUsageAction,
    GetVFolderUsedBytesAction,
    GetVolumePerfMetricAction,
    ListAllHostsAction,
    ListAllowedTypesAction,
    ListHostsAction,
    UpdateQuotaAction,
)
from ai.backend.manager.types import OptionalState

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class VFolderHandler:
    """VFolder API handler with typed parameter injection."""

    # ------------------------------------------------------------------
    # 1. create (POST /)
    # ------------------------------------------------------------------

    async def create(
        self,
        body: BodyParam[VFolderCreateReq],
        ctx: UserContext,
        req: RequestCtx,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        params = body.parsed
        user_role = req.request["user"]["role"]
        keypair_resource_policy = req.request["keypair"]["resource_policy"]

        group_id_or_name: str | uuid.UUID | None = None
        if params.group_id is not None:
            group_id_or_name = params.group_id

        log.info(
            "VFOLDER.CREATE (email:{}, ak:{}, vf:{}, vfh:{}, umod:{}, perm:{})",
            ctx.user_email,
            ctx.access_key,
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
            scope_id = str(ctx.user_uuid)

        try:
            result = await processors_ctx.processors.vfolder.create_vfolder.wait_for_complete(
                CreateVFolderAction(
                    name=params.name,
                    keypair_resource_policy=keypair_resource_policy,
                    domain_name=ctx.user_domain,
                    group_id_or_name=group_id_or_name,
                    folder_host=folder_host,
                    unmanaged_path=unmanaged_path,
                    mount_permission=VFolderPermission(params.permission.value),
                    usage_mode=params.usage_mode,
                    cloneable=params.cloneable,
                    user_uuid=ctx.user_uuid,
                    user_role=user_role,
                    creator_email=ctx.user_email,
                    _scope_type=scope_type,
                    _scope_id=scope_id,
                )
            )
        except (VFolderInvalidParameter, VFolderAlreadyExists) as e:
            raise InvalidAPIParameters(str(e)) from e
        except BackendAIError as e:
            raise InternalServerError(str(e)) from e

        item = VFolderItemField(
            id=result.id.hex,
            name=result.name,
            quota_scope_id=str(result.quota_scope_id),
            host=result.host,
            usage_mode=result.usage_mode,
            permission=VFolderPermissionField(result.mount_permission.value),
            max_size=0,
            creator=result.creator_email,
            ownership_type=VFolderOwnershipTypeField(result.ownership_type.value),
            user=(
                str(result.user_uuid)
                if result.ownership_type == VFolderOwnershipType.USER
                else None
            ),
            group=(
                str(result.group_uuid)
                if result.ownership_type == VFolderOwnershipType.GROUP
                else None
            ),
            cloneable=result.cloneable,
            status=VFolderOperationStatusField(result.status.value),
            is_owner=True,
            created_at="",
        )
        resp = VFolderCreateResponse(item=item)
        return APIResponse.build(HTTPStatus.CREATED, resp)

    # ------------------------------------------------------------------
    # 2. list_folders (GET /)
    # ------------------------------------------------------------------

    async def list_folders(
        self,
        query: QueryParam[ListVFoldersQuery],
        ctx: UserContext,
        req: RequestCtx,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        params = query.parsed
        log.info(
            "VFOLDER.LIST (email:{}, ak:{})",
            ctx.user_email,
            ctx.access_key,
        )
        owner_user_uuid, owner_user_role = await get_user_scopes(
            req.request,
            {
                "owner_user_email": params.owner_user_email,
            }
            if params.owner_user_email
            else None,
        )
        group_id = params.group_id
        if group_id is not None:
            scope_type = ScopeType.PROJECT
            scope_id = str(group_id)
        else:
            scope_type = ScopeType.USER
            scope_id = str(owner_user_uuid)
        result = await processors_ctx.processors.vfolder.list_vfolder.wait_for_complete(
            ListVFolderAction(
                user_uuid=owner_user_uuid,
                _scope_type=scope_type,
                _scope_id=scope_id,
            )
        )
        items: list[VFolderItemField] = []
        for base_info, ownership_info in result.vfolders:
            items.append(
                VFolderItemField(
                    name=base_info.name,
                    id=base_info.id.hex,
                    quota_scope_id=str(base_info.quota_scope_id),
                    host=base_info.host,
                    status=VFolderOperationStatusField(base_info.status.value),
                    usage_mode=base_info.usage_mode,
                    created_at=str(base_info.created_at),
                    is_owner=ownership_info.is_owner,
                    permission=VFolderPermissionField(base_info.mount_permission.value),
                    user=str(ownership_info.user_uuid) if ownership_info.user_uuid else None,
                    group=str(ownership_info.group_uuid) if ownership_info.group_uuid else None,
                    creator=ownership_info.creator_email or "",
                    ownership_type=VFolderOwnershipTypeField(ownership_info.ownership_type.value),
                    cloneable=base_info.cloneable,
                )
            )
        resp = VFolderListResponse(items=items)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 3. list_hosts (GET /_/hosts)
    # ------------------------------------------------------------------

    async def list_hosts(
        self,
        query: QueryParam[ListHostsQuery],
        ctx: UserContext,
        req: RequestCtx,
        procs: ProcessorsCtx,
    ) -> APIResponse:
        params = query.parsed
        log.info(
            "VFOLDER.LIST_HOSTS (email:{}, ak:{})",
            ctx.user_email,
            ctx.access_key,
        )
        resource_policy = req.request["keypair"]["resource_policy"]

        result = await procs.processors.vfolder.list_hosts.wait_for_complete(
            ListHostsAction(
                user_uuid=ctx.user_uuid,
                domain_name=ctx.user_domain,
                group_id=params.group_id,
                resource_policy=resource_policy,
            )
        )

        volume_info = {}
        for host_key, info in result.volume_info.items():
            volume_info[host_key] = VolumeInfoDTO(
                backend=info["backend"],
                capabilities=info["capabilities"],
                usage=info["usage"],
                sftp_scaling_groups=info["sftp_scaling_groups"],
            )

        resp = ListHostsResponse(
            default=result.default,
            allowed=result.allowed,
            volume_info=volume_info,
        )
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 4. list_all_hosts (GET /_/all-hosts)
    # ------------------------------------------------------------------

    async def list_all_hosts(
        self,
        ctx: UserContext,
        procs: ProcessorsCtx,
    ) -> APIResponse:
        log.info(
            "VFOLDER.LIST_ALL_HOSTS (email:{}, ak:{})",
            ctx.user_email,
            ctx.access_key,
        )
        result = await procs.processors.vfolder.list_all_hosts.wait_for_complete(
            ListAllHostsAction()
        )
        resp = ListAllHostsResponse(
            default=result.default,
            allowed=result.allowed,
        )
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 5. get_volume_perf_metric (GET /_/perf-metric)
    # ------------------------------------------------------------------

    async def get_volume_perf_metric(
        self,
        query: QueryParam[GetVolumePerfMetricQuery],
        ctx: UserContext,
        procs: ProcessorsCtx,
    ) -> APIResponse:
        params = query.parsed
        log.info(
            "VFOLDER.VOLUME_PERF_METRIC (email:{}, ak:{})",
            ctx.user_email,
            ctx.access_key,
        )
        result = await procs.processors.vfolder.get_volume_perf_metric.wait_for_complete(
            GetVolumePerfMetricAction(folder_host=params.folder_host)
        )
        resp = GetVolumePerfMetricResponse(data=result.data)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 6. list_allowed_types (GET /_/allowed-types)
    # ------------------------------------------------------------------

    async def list_allowed_types(
        self,
        ctx: UserContext,
        procs: ProcessorsCtx,
    ) -> APIResponse:
        log.info(
            "VFOLDER.LIST_ALLOWED_TYPES (email:{}, ak:{})",
            ctx.user_email,
            ctx.access_key,
        )
        result = await procs.processors.vfolder.list_allowed_types.wait_for_complete(
            ListAllowedTypesAction()
        )
        resp = ListAllowedTypesResponse(allowed_types=result.allowed_types)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 7. get_info (GET /{name})
    # ------------------------------------------------------------------

    async def get_info(
        self,
        vfctx: VFolderAuthContext,
        req: RequestCtx,
    ) -> APIResponse:
        row = vfctx.vfolder_row
        log.info(
            "VFOLDER.GETINFO (email:{}, ak:{}, vf:{} (resolved-from:{!r}))",
            vfctx.user_email,
            vfctx.access_key,
            row["id"],
            req.request.match_info["name"],
        )
        result = await vfctx.processors.vfolder.get_vfolder.wait_for_complete(
            GetVFolderAction(
                vfctx.user_uuid,
                vfolder_uuid=row["id"],
            )
        )
        dto = VFolderInfoDTO(
            name=result.base_info.name,
            id=result.base_info.id.hex,
            quota_scope_id=str(result.base_info.quota_scope_id),
            host=result.base_info.host,
            status=VFolderOperationStatusField(result.base_info.status.value),
            num_files=result.usage_info.num_files,
            used_bytes=result.usage_info.used_bytes,
            created_at=str(result.base_info.created_at),
            last_used=str(result.base_info.created_at),
            user=(
                str(result.ownership_info.user_uuid) if result.ownership_info.user_uuid else None
            ),
            group=(
                str(result.ownership_info.group_uuid) if result.ownership_info.group_uuid else None
            ),
            type="user" if result.ownership_info.user_uuid else "group",
            is_owner=result.ownership_info.is_owner,
            permission=VFolderPermissionField(result.base_info.mount_permission.value),
            usage_mode=result.base_info.usage_mode,
            cloneable=result.base_info.cloneable,
        )
        resp = VFolderGetInfoResponse(item=dto)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 8. get_quota (GET /_/quota)
    # ------------------------------------------------------------------

    async def get_quota(
        self,
        query: QueryParam[GetQuotaQuery],
        ctx: UserContext,
        req: RequestCtx,
        procs: ProcessorsCtx,
    ) -> APIResponse:
        params = query.parsed
        vfolder_row = (
            await resolve_vfolder_rows(req.request, VFolderPermissionSetAlias.READABLE, params.id)
        )[0]
        await check_vfolder_status(vfolder_row, VFolderStatusSet.READABLE)
        log.info(
            "VFOLDER.GET_QUOTA (email:{}, vf:{})",
            ctx.user_email,
            params.id,
        )

        user_role = req.request["user"]["role"]
        vfid = str(VFolderID.from_row(vfolder_row))

        result = await procs.processors.vfolder.get_quota.wait_for_complete(
            GetQuotaAction(
                folder_host=params.folder_host,
                vfid=vfid,
                vfolder_id=params.id,
                unmanaged_path=vfolder_row["unmanaged_path"],
                user_role=user_role,
                user_uuid=ctx.user_uuid,
                domain_name=ctx.user_domain,
            )
        )
        resp = GetQuotaResponse(data=result.data)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 9. update_quota (POST /_/quota)
    # ------------------------------------------------------------------

    async def update_quota(
        self,
        body: BodyParam[UpdateQuotaReq],
        ctx: UserContext,
        req: RequestCtx,
        procs: ProcessorsCtx,
    ) -> APIResponse:
        params = body.parsed
        vfolder_row = (
            await resolve_vfolder_rows(req.request, VFolderPermissionSetAlias.READABLE, params.id)
        )[0]
        await check_vfolder_status(vfolder_row, VFolderStatusSet.READABLE)
        quota = int(params.input["size_bytes"])
        log.info(
            "VFOLDER.UPDATE_QUOTA (email:{}, quota:{}, vf:{})",
            ctx.user_email,
            quota,
            params.id,
        )

        user_role = req.request["user"]["role"]
        resource_policy = req.request["keypair"]["resource_policy"]
        vfid = str(VFolderID.from_row(vfolder_row))

        result = await procs.processors.vfolder.update_quota.wait_for_complete(
            UpdateQuotaAction(
                folder_host=params.folder_host,
                vfid=vfid,
                vfolder_id=params.id,
                unmanaged_path=vfolder_row["unmanaged_path"],
                user_role=user_role,
                user_uuid=ctx.user_uuid,
                domain_name=ctx.user_domain,
                resource_policy=resource_policy,
                size_bytes=quota,
            )
        )
        resp = UpdateQuotaResponse(size_bytes=result.size_bytes)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 10. get_usage (GET /_/usage)
    # ------------------------------------------------------------------

    async def get_usage(
        self,
        query: QueryParam[GetUsageQuery],
        ctx: UserContext,
        req: RequestCtx,
        procs: ProcessorsCtx,
    ) -> APIResponse:
        params = query.parsed
        vfolder_row = (
            await resolve_vfolder_rows(req.request, VFolderPermissionSetAlias.READABLE, params.id)
        )[0]
        await check_vfolder_status(vfolder_row, VFolderStatusSet.READABLE)
        log.info(
            "VFOLDER.GET_USAGE (email:{}, vf:{})",
            ctx.user_email,
            params.id,
        )
        result = await procs.processors.vfolder.get_usage.wait_for_complete(
            GetVFolderUsageAction(
                folder_host=params.folder_host,
                vfolder_id=str(VFolderID(vfolder_row["quota_scope_id"], params.id)),
                unmanaged_path=vfolder_row["unmanaged_path"],
            )
        )
        resp = GetUsageResponse(data=result.data)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 11. get_used_bytes (GET /_/used-bytes)
    # ------------------------------------------------------------------

    async def get_used_bytes(
        self,
        query: QueryParam[GetUsedBytesQuery],
        ctx: UserContext,
        req: RequestCtx,
        procs: ProcessorsCtx,
    ) -> APIResponse:
        params = query.parsed
        vfolder_row = (
            await resolve_vfolder_rows(req.request, VFolderPermissionSetAlias.READABLE, params.id)
        )[0]
        await check_vfolder_status(vfolder_row, VFolderStatusSet.READABLE)
        log.info("VFOLDER.GET_USED_BYTES (vf:{})", params.id)
        result = await procs.processors.vfolder.get_used_bytes.wait_for_complete(
            GetVFolderUsedBytesAction(
                folder_host=params.folder_host,
                vfolder_id=str(VFolderID(vfolder_row["quota_scope_id"], params.id)),
                unmanaged_path=vfolder_row["unmanaged_path"],
            )
        )
        resp = GetUsedBytesResponse(data=result.data)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 12. rename_vfolder (POST /{name}/rename)
    # ------------------------------------------------------------------

    async def rename_vfolder(
        self,
        body: BodyParam[RenameVFolderReq],
        vfctx: VFolderAuthContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        row = vfctx.vfolder_row
        new_name = params.new_name
        log.info(
            "VFOLDER.RENAME (email:{}, ak:{}, vf:{} (resolved-from:{!r}), new-name:{})",
            vfctx.user_email,
            vfctx.access_key,
            row["id"],
            req.request.match_info["name"],
            new_name,
        )

        updater_spec = VFolderAttributeUpdaterSpec(
            name=OptionalState[str].update(new_name),
        )
        await vfctx.processors.vfolder.update_vfolder_attribute.wait_for_complete(
            UpdateVFolderAttributeAction(
                user_uuid=vfctx.user_uuid,
                vfolder_uuid=row["id"],
                updater=Updater(
                    spec=updater_spec,
                    pk_value=row["id"],
                ),
            )
        )
        return APIResponse.no_content(HTTPStatus.CREATED)

    # ------------------------------------------------------------------
    # 13. update_vfolder_options (POST /{name}/update-options)
    # ------------------------------------------------------------------

    async def update_vfolder_options(
        self,
        body: BodyParam[UpdateVFolderOptionsReq],
        vfctx: VFolderAuthContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        row = vfctx.vfolder_row
        log.info(
            "VFOLDER.UPDATE_OPTIONS (email:{}, ak:{}, vf:{} (resolved-from:{!r}))",
            vfctx.user_email,
            vfctx.access_key,
            row["id"],
            req.request.match_info["name"],
        )
        cloneable = (
            OptionalState[bool].update(params.cloneable)
            if params.cloneable is not None
            else OptionalState[bool].nop()
        )
        mount_permission = (
            OptionalState[VFolderPermission].update(VFolderPermission(params.permission.value))
            if params.permission is not None
            else OptionalState[VFolderPermission].nop()
        )
        await vfctx.processors.vfolder.update_vfolder_attribute.wait_for_complete(
            UpdateVFolderAttributeAction(
                user_uuid=vfctx.user_uuid,
                vfolder_uuid=row["id"],
                updater=Updater(
                    spec=VFolderAttributeUpdaterSpec(
                        cloneable=cloneable,
                        mount_permission=mount_permission,
                    ),
                    pk_value=row["id"],
                ),
            )
        )
        return APIResponse.no_content(HTTPStatus.CREATED)

    # ------------------------------------------------------------------
    # 14. mkdir (POST /{name}/mkdir)
    # ------------------------------------------------------------------

    async def mkdir(
        self,
        body: BodyParam[MkdirReq],
        vfctx: VFolderAuthContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        row = vfctx.vfolder_row
        log.info(
            "VFOLDER.MKDIR (email:{}, ak:{}, vf:{} (resolved-from:{!r}), paths:{})",
            vfctx.user_email,
            vfctx.access_key,
            row["id"],
            req.request.match_info["name"],
            params.path,
        )

        result = await vfctx.processors.vfolder_file.mkdir.wait_for_complete(
            MkdirAction(
                user_id=vfctx.user_uuid,
                vfolder_uuid=row["id"],
                path=params.path,
                parents=params.parents,
                exist_ok=params.exist_ok,
            )
        )
        resp = MkdirResponse(results=cast(list[Any], result.results))
        return APIResponse.build(result.storage_resp_status, resp)

    # ------------------------------------------------------------------
    # 15. create_download_session (POST /{name}/request-download)
    # ------------------------------------------------------------------

    async def create_download_session(
        self,
        body: BodyParam[CreateDownloadSessionReq],
        vfctx: VFolderAuthContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        row = vfctx.vfolder_row
        log.info(
            "VFOLDER.CREATE_DOWNLOAD_SESSION(email:{}, ak:{}, vf:{} (resolved-from:{!r}), path:{})",
            vfctx.user_email,
            vfctx.access_key,
            row["id"],
            req.request.match_info["name"],
            params.path,
        )
        result = await vfctx.processors.vfolder_file.download_file.wait_for_complete(
            CreateDownloadSessionAction(
                user_uuid=vfctx.user_uuid,
                keypair_resource_policy=req.request["keypair"]["resource_policy"],
                vfolder_uuid=row["id"],
                path=params.path,
                archive=params.archive,
            )
        )
        resp = CreateDownloadSessionResponse(token=result.token, url=result.url)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 16. create_archive_download_session (POST /{name}/request-download-archive)
    # ------------------------------------------------------------------

    async def create_archive_download_session(
        self,
        body: BodyParam[CreateDownloadSessionReq],
        vfctx: VFolderAuthContext,
        req: RequestCtx,
    ) -> APIResponse:
        """Create a download session for archived files.

        Reuses CreateDownloadSessionReq body param -- the caller must supply
        ``files`` in the JSON body.  Since the existing legacy handler read
        ``params["files"]`` from a trafaret schema, we fall back to reading
        ``files`` from the raw request body when the DTO does not carry it.
        """
        row = vfctx.vfolder_row
        # The legacy endpoint expects a "files" list, not the single-file "path"
        # used by the normal download session.  Read directly from the request
        # body to maintain backward compatibility.
        raw_body = await req.request.json()
        files: list[str] = raw_body.get("files", [])
        log.info(
            "VFOLDER.CREATE_ARCHIVE_DOWNLOAD_SESSION"
            "(email:{}, ak:{}, vf:{} (resolved-from:{!r}), files:{})",
            vfctx.user_email,
            vfctx.access_key,
            row["id"],
            req.request.match_info["name"],
            files,
        )
        result = (
            await vfctx.processors.vfolder_file.create_archive_download_session.wait_for_complete(
                CreateArchiveDownloadSessionAction(
                    keypair_resource_policy=req.request["keypair"]["resource_policy"],
                    vfolder_uuid=row["id"],
                    files=files,
                )
            )
        )
        resp = CreateDownloadSessionResponse(token=result.token, url=result.url)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 17. create_upload_session (POST /{name}/request-upload)
    # ------------------------------------------------------------------

    async def create_upload_session(
        self,
        body: BodyParam[CreateUploadSessionReq],
        vfctx: VFolderAuthContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        row = vfctx.vfolder_row
        log.info(
            "VFOLDER.CREATE_UPLOAD_SESSION (email:{}, ak:{}, vf:{} (resolved-from:{!r}), path:{})",
            vfctx.user_email,
            vfctx.access_key,
            row["id"],
            req.request.match_info["name"],
            params.path,
        )
        result = await vfctx.processors.vfolder_file.upload_file.wait_for_complete(
            CreateUploadSessionAction(
                user_uuid=vfctx.user_uuid,
                keypair_resource_policy=req.request["keypair"]["resource_policy"],
                vfolder_uuid=row["id"],
                path=params.path,
                size=str(params.size),
            )
        )
        resp = CreateUploadSessionResponse(token=result.token, url=result.url)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 18. rename_file (POST /{name}/rename-file)
    # ------------------------------------------------------------------

    async def rename_file(
        self,
        body: BodyParam[RenameFileReq],
        vfctx: VFolderAuthContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        row = vfctx.vfolder_row
        log.info(
            "VFOLDER.RENAME_FILE (email:{}, ak:{}, vf:{} (resolved-from:{!r}), "
            "target_path:{}, new_name:{})",
            vfctx.user_email,
            vfctx.access_key,
            row["id"],
            req.request.match_info["name"],
            params.target_path,
            params.new_name,
        )
        await vfctx.processors.vfolder_file.rename_file.wait_for_complete(
            RenameFileAction(
                user_uuid=vfctx.user_uuid,
                keypair_resource_policy=req.request["keypair"]["resource_policy"],
                vfolder_uuid=row["id"],
                target_path=params.target_path,
                new_name=params.new_name,
            )
        )
        resp = MessageResponse(msg="")
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 19. move_file (POST /{name}/move-file)
    # ------------------------------------------------------------------

    async def move_file(
        self,
        body: BodyParam[MoveFileReq],
        vfctx: VFolderAuthContext,
    ) -> APIResponse:
        params = body.parsed
        row = vfctx.vfolder_row
        log.info(
            "VFOLDER.MOVE_FILE (email:{}, ak:{}, vf:{}, src:{}, dst:{})",
            vfctx.user_email,
            vfctx.access_key,
            row["id"],
            params.src,
            params.dst,
        )
        await vfctx.processors.vfolder_file.move_file.wait_for_complete(
            MoveFileAction(
                user_uuid=vfctx.user_uuid,
                vfolder_uuid=row["id"],
                src=params.src,
                dst=params.dst,
            )
        )
        resp = MessageResponse(msg="")
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 20. delete_files (POST/DELETE /{name}/delete-files)
    # ------------------------------------------------------------------

    async def delete_files(
        self,
        body: BodyParam[DeleteFilesReq],
        vfctx: VFolderAuthContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        row = vfctx.vfolder_row
        log.info(
            "VFOLDER.DELETE_FILES (email:{}, ak:{}, vf:{} (resolved-from:{!r}), "
            "path:{}, recursive:{})",
            vfctx.user_email,
            vfctx.access_key,
            row["id"],
            req.request.match_info["name"],
            params.files,
            params.recursive,
        )
        await vfctx.processors.vfolder_file.delete_files.wait_for_complete(
            DeleteFilesAction(
                user_uuid=vfctx.user_uuid,
                vfolder_uuid=row["id"],
                files=params.files,
                recursive=params.recursive,
            )
        )
        resp = MessageResponse(msg="")
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 21. delete_files_async (POST /{name}/delete-files-async)
    # ------------------------------------------------------------------

    async def delete_files_async(
        self,
        body: BodyParam[DeleteFilesAsyncBodyParam],
        vfctx: VFolderAuthContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        row = vfctx.vfolder_row
        log.info(
            "VFOLDER.DELETE_FILES_ASYNC (email:{}, ak:{}, vf:{} (resolved-from:{!r}), "
            "files:{}, recursive:{})",
            vfctx.user_email,
            vfctx.access_key,
            row["id"],
            req.request.match_info["name"],
            params.files,
            params.recursive,
        )

        result = await vfctx.processors.vfolder_file.delete_files_async.wait_for_complete(
            DeleteFilesAsyncAction(
                user_uuid=vfctx.user_uuid,
                vfolder_uuid=row["id"],
                files=params.files,
                recursive=params.recursive,
            )
        )

        resp = DeleteFilesAsyncResponse(bgtask_id=result.task_id)
        return APIResponse.build(HTTPStatus.ACCEPTED, resp)

    # ------------------------------------------------------------------
    # 22. list_files (GET /{name}/files)
    # ------------------------------------------------------------------

    async def list_files(
        self,
        query: QueryParam[ListFilesQuery],
        vfctx: VFolderAuthContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = query.parsed
        row = vfctx.vfolder_row
        log.info(
            "VFOLDER.LIST_FILES (email:{}, ak:{}, vf:{} (resolved-from:{!r}), path:{})",
            vfctx.user_email,
            vfctx.access_key,
            row["id"],
            req.request.match_info["name"],
            params.path,
        )
        result = await vfctx.processors.vfolder_file.list_files.wait_for_complete(
            ListFilesAction(
                user_uuid=vfctx.user_uuid,
                vfolder_uuid=row["id"],
                path=params.path,
            )
        )
        resp = ListFilesResponse(
            items=[info.to_json() for info in result.files],
        )
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 23. list_sent_invitations (GET /invitations/list-sent)
    # ------------------------------------------------------------------

    async def list_sent_invitations(
        self,
        ctx: UserContext,
        procs: ProcessorsCtx,
    ) -> APIResponse:
        log.info(
            "VFOLDER.LIST_SENT_INVITATIONS (email:{}, ak:{})",
            ctx.user_email,
            ctx.access_key,
        )
        result = await procs.processors.vfolder_invite.list_sent_invitations.wait_for_complete(
            ListSentInvitationsAction(requester_user_uuid=ctx.user_uuid)
        )
        invs_info = []
        for inv in result.invitations:
            invs_info.append(
                VFolderInvitationDTO(
                    id=str(inv.id),
                    inviter=inv.inviter_user_email,
                    invitee=inv.invitee_user_email,
                    perm=VFolderPermissionField(inv.mount_permission.value),
                    state=inv.status.value,
                    created_at=str(inv.created_at),
                    modified_at=str(inv.modified_at),
                    vfolder_id=str(inv.vfolder_id),
                    vfolder_name=inv.vfolder_name,
                )
            )
        resp = ListSentInvitationsResponse(invitations=invs_info)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 24. update_invitation (POST /invitations/update/{inv_id})
    # ------------------------------------------------------------------

    async def update_invitation(
        self,
        body: BodyParam[UpdateInvitationReq],
        ctx: UserContext,
        req: RequestCtx,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        params = body.parsed
        inv_id = req.request.match_info["inv_id"]
        log.info(
            "VFOLDER.UPDATE_INVITATION (email:{}, ak:{}, inv:{})",
            ctx.user_email,
            ctx.access_key,
            inv_id,
        )
        await processors_ctx.processors.vfolder_invite.update_invitation.wait_for_complete(
            UpdateInvitationAction(
                invitation_id=uuid.UUID(inv_id),
                requester_user_uuid=ctx.user_uuid,
                mount_permission=VFolderPermission(params.permission.value),
            )
        )
        resp = MessageResponse(msg=f"vfolder invitation updated: {inv_id}.")
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 25. invite (POST /{name}/invite)
    # ------------------------------------------------------------------

    async def invite(
        self,
        body: BodyParam[InviteVFolderReq],
        vfctx: VFolderAuthContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        row = vfctx.vfolder_row
        perm = VFolderPermission(params.permission.value)
        invitee_emails = params.emails
        log.info(
            "VFOLDER.INVITE (email:{}, ak:{}, vf:{} (resolved-from:{!r}), inv.users:{})",
            vfctx.user_email,
            vfctx.access_key,
            row["id"],
            req.request.match_info["name"],
            ",".join(invitee_emails),
        )
        result = await vfctx.processors.vfolder_invite.invite_vfolder.wait_for_complete(
            InviteVFolderAction(
                keypair_resource_policy=req.request["keypair"]["resource_policy"],
                user_uuid=vfctx.user_uuid,
                vfolder_uuid=row["id"],
                mount_permission=perm,
                invitee_emails=invitee_emails,
            )
        )
        resp = InviteVFolderResponse(invited_ids=result.invitation_ids)
        return APIResponse.build(HTTPStatus.CREATED, resp)

    # ------------------------------------------------------------------
    # 26. invitations (GET /invitations/list)
    # ------------------------------------------------------------------

    async def invitations(
        self,
        ctx: UserContext,
        req: RequestCtx,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        log.info(
            "VFOLDER.INVITATIONS (email:{}, ak:{})",
            ctx.user_email,
            ctx.access_key,
        )
        result = await processors_ctx.processors.vfolder_invite.list_invitation.wait_for_complete(
            ListInvitationAction(
                requester_user_uuid=ctx.user_uuid,
            )
        )
        invs = []
        for info in result.info:
            inv_json = info.to_json()
            inv_json["perm"] = info.mount_permission.value
            invs.append(
                VFolderInvitationDTO(
                    id=inv_json.get("id", ""),
                    inviter=inv_json.get("inviter", ""),
                    invitee=inv_json.get("invitee", ""),
                    perm=VFolderPermissionField(info.mount_permission.value),
                    state=inv_json.get("state", ""),
                    created_at=inv_json.get("created_at", ""),
                    modified_at=inv_json.get("modified_at"),
                    vfolder_id=inv_json.get("vfolder_id", ""),
                    vfolder_name=inv_json.get("vfolder_name", ""),
                )
            )
        resp = ListInvitationsResponse(invitations=invs)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 27. accept_invitation (POST /invitations/accept)
    # ------------------------------------------------------------------

    async def accept_invitation(
        self,
        body: BodyParam[AcceptInvitationReq],
        ctx: UserContext,
        req: RequestCtx,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        params = body.parsed
        inv_id = params.inv_id
        log.info(
            "VFOLDER.ACCEPT_INVITATION (email:{}, ak:{}, inv:{})",
            ctx.user_email,
            ctx.access_key,
            inv_id,
        )
        await processors_ctx.processors.vfolder_invite.accept_invitation.wait_for_complete(
            AcceptInvitationAction(
                invitation_id=uuid.UUID(inv_id),
            )
        )
        resp = MessageResponse(msg="")
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 28. delete_invitation (POST/DELETE /invitations/delete)
    # ------------------------------------------------------------------

    async def delete_invitation(
        self,
        body: BodyParam[DeleteInvitationReq],
        ctx: UserContext,
        req: RequestCtx,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        params = body.parsed
        inv_id = params.inv_id
        log.info(
            "VFOLDER.DELETE_INVITATION (email:{}, ak:{}, inv:{})",
            ctx.user_email,
            ctx.access_key,
            inv_id,
        )
        await processors_ctx.processors.vfolder_invite.reject_invitation.wait_for_complete(
            RejectInvitationAction(
                invitation_id=uuid.UUID(inv_id),
                requester_user_uuid=ctx.user_uuid,
            )
        )
        resp = MessageResponse(msg="")
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 29. share (POST /{name}/share)
    # ------------------------------------------------------------------

    async def share(
        self,
        body: BodyParam[ShareVFolderReq],
        vfctx: VFolderAuthContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        row = vfctx.vfolder_row
        log.info(
            "VFOLDER.SHARE (email:{}, ak:{}, vf:{} (resolved-from:{!r}), perm:{}, users:{})",
            vfctx.user_email,
            vfctx.access_key,
            row["id"],
            req.request.match_info["name"],
            params.permission,
            ",".join(params.emails),
        )
        result = await vfctx.processors.vfolder_sharing.share.wait_for_complete(
            ShareVFolderAction(
                user_uuid=vfctx.user_uuid,
                vfolder_uuid=row["id"],
                resource_policy=req.request["keypair"]["resource_policy"],
                permission=VFolderPermission(params.permission.value),
                emails=params.emails,
            )
        )
        resp = ShareVFolderResponse(shared_emails=result.shared_emails)
        return APIResponse.build(HTTPStatus.CREATED, resp)

    # ------------------------------------------------------------------
    # 30. unshare (POST/DELETE /{name}/unshare)
    # ------------------------------------------------------------------

    async def unshare(
        self,
        body: BodyParam[UnshareVFolderReq],
        vfctx: VFolderAuthContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        row = vfctx.vfolder_row
        log.info(
            "VFOLDER.UNSHARE (email:{}, ak:{}, vf:{} (resolved-from:{!r}), users:{})",
            vfctx.user_email,
            vfctx.access_key,
            row["id"],
            req.request.match_info["name"],
            ",".join(params.emails),
        )
        result = await vfctx.processors.vfolder_sharing.unshare.wait_for_complete(
            UnshareVFolderAction(
                user_uuid=vfctx.user_uuid,
                vfolder_uuid=row["id"],
                resource_policy=req.request["keypair"]["resource_policy"],
                emails=params.emails,
            )
        )
        resp = UnshareVFolderResponse(unshared_emails=result.unshared_emails)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 31. delete_by_id (DELETE /)
    # ------------------------------------------------------------------

    async def delete_by_id(
        self,
        body: BodyParam[DeleteVFolderByIDReq],
        ctx: UserContext,
        req: RequestCtx,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        params = body.parsed
        resource_policy = req.request["keypair"]["resource_policy"]
        folder_id = params.vfolder_id

        log.info(
            "VFOLDER.DELETE_BY_ID (email:{}, ak:{}, vf:{})",
            ctx.user_email,
            ctx.access_key,
            folder_id,
        )
        try:
            await processors_ctx.processors.vfolder.move_to_trash_vfolder.wait_for_complete(
                MoveToTrashVFolderAction(
                    user_uuid=ctx.user_uuid,
                    keypair_resource_policy=resource_policy,
                    vfolder_uuid=folder_id,
                )
            )
        except VFolderInvalidParameter as e:
            raise InvalidAPIParameters(str(e)) from e

        return APIResponse.no_content(HTTPStatus.NO_CONTENT)

    # ------------------------------------------------------------------
    # 32. delete_by_name (DELETE /{name})
    # ------------------------------------------------------------------

    async def delete_by_name(
        self,
        ctx: UserContext,
        req: RequestCtx,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        resource_policy = req.request["keypair"]["resource_policy"]
        folder_name = req.request.match_info["name"]

        rows = await resolve_vfolder_rows(
            req.request,
            VFolderPermissionSetAlias.READABLE,
            folder_name,
            allow_privileged_access=True,
        )
        if len(rows) > 1:
            raise TooManyVFoldersFound(rows)
        row = rows[0]
        log.info(
            "VFOLDER.DELETE_BY_NAME (email:{}, ak:{}, vf:{} (resolved-from:{!r}))",
            ctx.user_email,
            ctx.access_key,
            row["id"],
            folder_name,
        )
        try:
            await processors_ctx.processors.vfolder.move_to_trash_vfolder.wait_for_complete(
                MoveToTrashVFolderAction(
                    user_uuid=ctx.user_uuid,
                    keypair_resource_policy=resource_policy,
                    vfolder_uuid=row["id"],
                )
            )
        except VFolderInvalidParameter as e:
            raise InvalidAPIParameters(str(e)) from e
        return APIResponse.no_content(HTTPStatus.NO_CONTENT)

    # ------------------------------------------------------------------
    # 33. get_vfolder_id (GET /_/id)
    # ------------------------------------------------------------------

    async def get_vfolder_id(
        self,
        query: QueryParam[GetVFolderIDReq],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = query.parsed
        folder_name = params.name
        rows = await resolve_vfolder_rows(
            req.request,
            VFolderPermissionSetAlias.READABLE,
            folder_name,
            allow_privileged_access=True,
        )
        if len(rows) > 1:
            raise TooManyVFoldersFound(rows)
        row = rows[0]
        log.info(
            "VFOLDER.GET_ID (email:{}, ak:{}, vf:{} (resolved-from:{!r}))",
            ctx.user_email,
            ctx.access_key,
            row["id"],
            folder_name,
        )
        dto = CompactVFolderInfoDTO(id=row["id"], name=folder_name)
        resp = VFolderGetIDResponse(item=dto)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 34. delete_from_trash_bin (POST /delete-from-trash-bin)
    # ------------------------------------------------------------------

    async def delete_from_trash_bin(
        self,
        body: BodyParam[DeleteVFolderFromTrashReq],
        ctx: UserContext,
        req: RequestCtx,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        params = body.parsed
        folder_id = params.vfolder_id
        user_uuid = ctx.user_uuid

        log.info(
            "VFOLDER.DELETE_FROM_TRASH_BIN (email:{}, ak:{}, vf:{})",
            ctx.user_email,
            ctx.access_key,
            folder_id,
        )
        try:
            await processors_ctx.processors.vfolder.delete_forever_vfolder.wait_for_complete(
                DeleteForeverVFolderAction(
                    user_uuid=user_uuid,
                    vfolder_uuid=folder_id,
                )
            )
        except VFolderInvalidParameter as e:
            raise InvalidAPIParameters(str(e)) from e
        except TooManyVFoldersFound as e:
            raise InternalServerError("Too many vfolders found") from e

        return APIResponse.no_content(HTTPStatus.NO_CONTENT)

    # ------------------------------------------------------------------
    # 35. force_delete (DELETE /{folder_id}/force)
    # ------------------------------------------------------------------

    async def force_delete(
        self,
        ctx: UserContext,
        req: RequestCtx,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        piece = req.request.match_info["folder_id"]
        try:
            folder_id = uuid.UUID(piece)
        except ValueError as e:
            raise InvalidAPIParameters(f"Not allowed UUID type value ({piece})") from e

        await processors_ctx.processors.vfolder.force_delete_vfolder.wait_for_complete(
            ForceDeleteVFolderAction(
                user_uuid=ctx.user_uuid,
                vfolder_uuid=folder_id,
            )
        )
        return APIResponse.no_content(HTTPStatus.NO_CONTENT)

    # ------------------------------------------------------------------
    # 36. purge (POST /purge)
    # ------------------------------------------------------------------

    async def purge(
        self,
        body: BodyParam[PurgeVFolderReq],
        ctx: UserContext,
        req: RequestCtx,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        params = body.parsed
        folder_id = params.vfolder_id
        log.info(
            "VFOLDER.PURGE (email:{}, ak:{}, vf:{})",
            ctx.user_email,
            ctx.access_key,
            folder_id,
        )
        user_role = req.request["user"]["role"]
        if user_role not in (
            UserRole.ADMIN,
            UserRole.SUPERADMIN,
        ):
            raise InsufficientPrivilege("You are not allowed to purge vfolders")

        await processors_ctx.processors.vfolder.purge_vfolder.wait_for_complete(
            PurgeVFolderAction(
                purger=RBACEntityPurger(
                    row_class=VFolderRow,
                    pk_value=folder_id,
                    spec=VFolderPurgerSpec(vfolder_id=folder_id),
                ),
            )
        )

        return APIResponse.no_content(HTTPStatus.NO_CONTENT)

    # ------------------------------------------------------------------
    # 37. restore (POST /restore-from-trash-bin)
    # ------------------------------------------------------------------

    async def restore(
        self,
        body: BodyParam[RestoreVFolderReq],
        ctx: UserContext,
        req: RequestCtx,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        params = body.parsed
        folder_id = params.vfolder_id
        user_uuid = ctx.user_uuid
        log.info(
            "VFOLDER.RESTORE (email:{}, ak:{}, vf:{})",
            ctx.user_email,
            ctx.access_key,
            folder_id,
        )

        await processors_ctx.processors.vfolder.restore_vfolder_from_trash.wait_for_complete(
            RestoreVFolderFromTrashAction(
                user_uuid=user_uuid,
                vfolder_uuid=folder_id,
            )
        )
        return APIResponse.no_content(HTTPStatus.NO_CONTENT)

    # ------------------------------------------------------------------
    # 38. leave (POST /{name}/leave)
    # ------------------------------------------------------------------

    async def leave(
        self,
        body: BodyParam[LeaveVFolderReq],
        vfctx: VFolderAuthContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        row = vfctx.vfolder_row
        vfolder_id = row["id"]
        perm = row["permission"]

        log.info(
            "VFOLDER.LEAVE(email:{}, ak:{}, vf:{} (resolved-from:{!r}), uid:{}, perm:{})",
            vfctx.user_email,
            vfctx.access_key,
            vfolder_id,
            req.request.match_info["name"],
            vfctx.user_uuid,
            perm,
        )
        if row["ownership_type"] == VFolderOwnershipType.GROUP:
            raise InvalidAPIParameters("Cannot leave a group vfolder.")
        await vfctx.processors.vfolder_invite.leave_invited_vfolder.wait_for_complete(
            LeaveInvitedVFolderAction(
                vfolder_uuid=vfolder_id,
                requester_user_uuid=vfctx.user_uuid,
                shared_user_uuid=(
                    uuid.UUID(params.shared_user_uuid)
                    if params.shared_user_uuid is not None
                    else None
                ),
            )
        )
        resp = MessageResponse(msg="left the shared vfolder")
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 39. clone (POST /{name}/clone)
    # ------------------------------------------------------------------

    async def clone(
        self,
        body: BodyParam[CloneVFolderReq],
        vfctx: VFolderAuthContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        row = vfctx.vfolder_row
        log.info(
            "VFOLDER.CLONE (email:{}, ak:{}, vf:{} (resolved-from:{!r}), "
            "vft:{}, vfh:{}, umod:{}, perm:{})",
            vfctx.user_email,
            vfctx.access_key,
            row["id"],
            req.request.match_info["name"],
            params.target_name,
            params.target_host,
            params.usage_mode.value,
            params.permission.value,
        )

        result = await vfctx.processors.vfolder.clone_vfolder.wait_for_complete(
            CloneVFolderAction(
                requester_user_uuid=vfctx.user_uuid,
                source_vfolder_uuid=row["id"],
                target_name=params.target_name,
                target_host=params.target_host,
                cloneable=params.cloneable,
                usage_mode=params.usage_mode,
                mount_permission=VFolderPermission(params.permission.value),
            )
        )
        dto = VFolderCloneInfoDTO(
            id=result.target_vfolder_id.hex,
            name=params.target_name,
            host=result.target_vfolder_host,
            usage_mode=result.usage_mode,
            permission=VFolderPermissionField(result.mount_permission.value),
            creator=vfctx.user_email,
            ownership_type=VFolderOwnershipTypeField(result.ownership_type.value),
            user=str(result.owner_user_uuid) if result.owner_user_uuid is not None else None,
            group=str(result.owner_group_uuid) if result.owner_group_uuid is not None else None,
            cloneable=params.cloneable,
            bgtask_id=str(result.bgtask_id),
        )
        resp = VFolderCloneResponse(item=dto)
        return APIResponse.build(HTTPStatus.CREATED, resp)

    # ------------------------------------------------------------------
    # 40. list_shared_vfolders (GET /_/shared)
    # ------------------------------------------------------------------

    async def list_shared_vfolders(
        self,
        query: QueryParam[ListSharedVFoldersQuery],
        ctx: UserContext,
        procs: ProcessorsCtx,
    ) -> APIResponse:
        params = query.parsed
        target_vfid = params.vfolder_id
        log.info(
            "VFOLDER.LIST_SHARED_VFOLDERS (email:{}, ak:{}, vf:{})",
            ctx.user_email,
            ctx.access_key,
            target_vfid,
        )
        result = await procs.processors.vfolder_sharing.list_shared.wait_for_complete(
            ListSharedVFoldersAction(vfolder_id=target_vfid)
        )
        shared_info = []
        for shared in result.shared:
            shared_info.append(
                VFolderSharedInfoDTO(
                    vfolder_id=str(shared.vfolder_id),
                    vfolder_name=shared.vfolder_name,
                    status=shared.status.value,
                    owner=shared.owner,
                    type=shared.folder_type,
                    shared_to={
                        "uuid": str(shared.shared_user_uuid),
                        "email": shared.shared_user_email,
                    },
                    perm=VFolderPermissionField(shared.permission.value),
                )
            )
        resp = ListSharedVFoldersResponse(shared=shared_info)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 41. update_shared_vfolder (POST /_/shared)
    # ------------------------------------------------------------------

    async def update_shared_vfolder(
        self,
        body: BodyParam[UpdateSharedVFolderReq],
        ctx: UserContext,
        req: RequestCtx,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        params = body.parsed
        vfolder_id = params.vfolder
        user_uuid = params.user
        perm = VFolderPermission(params.permission.value) if params.permission is not None else None
        log.info(
            "VFOLDER.UPDATE_SHARED_VFOLDER(email:{}, ak:{}, vf:{}, uid:{}, perm:{})",
            ctx.user_email,
            ctx.access_key,
            vfolder_id,
            user_uuid,
            perm,
        )
        if perm is not None:
            await processors_ctx.processors.vfolder_invite.update_invited_vfolder_mount_permission.wait_for_complete(
                UpdateInvitedVFolderMountPermissionAction(
                    vfolder_id=vfolder_id,
                    user_id=user_uuid,
                    permission=perm,
                )
            )
        else:
            await processors_ctx.processors.vfolder_invite.revoke_invited_vfolder.wait_for_complete(
                RevokeInvitedVFolderAction(vfolder_id=vfolder_id, shared_user_id=user_uuid)
            )
        resp = MessageResponse(msg="shared vfolder permission updated")
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 42. update_vfolder_sharing_status (POST /_/sharing)
    # ------------------------------------------------------------------

    async def update_vfolder_sharing_status(
        self,
        body: BodyParam[UpdateVFolderSharingStatusReq],
        ctx: UserContext,
        procs: ProcessorsCtx,
    ) -> APIResponse:
        params = body.parsed
        vfolder_id = params.vfolder_id
        user_perm_list = params.user_perm_list
        log.info(
            "VFOLDER.UPDATE_VFOLDER_SHARING_STATUS(email:{}, ak:{}, vf:{}, data:{})",
            ctx.user_email,
            ctx.access_key,
            vfolder_id,
            user_perm_list,
        )

        to_delete: list[uuid.UUID] = []
        to_update: list[tuple[uuid.UUID, VFolderPermission]] = []
        for mapping in user_perm_list:
            if mapping.perm is None:
                to_delete.append(mapping.user_id)
            else:
                to_update.append((mapping.user_id, VFolderPermission(mapping.perm.value)))

        await procs.processors.vfolder_sharing.update_sharing_status.wait_for_complete(
            UpdateVFolderSharingStatusAction(
                vfolder_id=vfolder_id,
                to_delete=to_delete,
                to_update=to_update,
            )
        )
        return APIResponse.no_content(HTTPStatus.CREATED)

    # ------------------------------------------------------------------
    # 43. get_fstab_contents (GET /_/fstab)
    # ------------------------------------------------------------------

    async def get_fstab_contents(
        self,
        query: QueryParam[GetFstabContentsQuery],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = query.parsed
        log.info(
            "VFOLDER.GET_FSTAB_CONTENTS(email:{}, ak:{}, ag:{})",
            ctx.user_email,
            ctx.access_key,
            params.agent_id,
        )
        fstab_path = params.fstab_path
        if fstab_path is None:
            fstab_path = "/etc/fstab"
        if params.agent_id is not None:
            watcher_info = await get_watcher_info(req.request, params.agent_id)
            try:
                client_timeout = aiohttp.ClientTimeout(total=10.0)
                async with aiohttp.ClientSession(timeout=client_timeout) as sess:
                    headers = {"X-BackendAI-Watcher-Token": watcher_info["token"]}
                    url = watcher_info["addr"] / "fstab"
                    query_params = {"fstab_path": fstab_path}
                    async with sess.get(url, headers=headers, params=query_params) as watcher_resp:
                        if watcher_resp.status == 200:
                            content = await watcher_resp.text()
                            resp = GetFstabContentsResponse(
                                content=content,
                                node="agent",
                                node_id=params.agent_id,
                            )
                            return APIResponse.build(HTTPStatus.OK, resp)
                        message = await watcher_resp.text()
                        raise BackendAgentError(
                            "FAILURE",
                            f"({watcher_resp.status}: {watcher_resp.reason}) {message}",
                        )
            except asyncio.CancelledError:
                raise
            except TimeoutError as e:
                log.error(
                    "VFOLDER.GET_FSTAB_CONTENTS(u:{}): timeout from watcher (agent:{})",
                    ctx.access_key,
                    params.agent_id,
                )
                raise BackendAgentError("TIMEOUT", "Could not fetch fstab data from agent") from e
            except Exception as e:
                log.exception(
                    "VFOLDER.GET_FSTAB_CONTENTS(u:{}): "
                    "unexpected error while reading from watcher (agent:{})",
                    ctx.access_key,
                    params.agent_id,
                )
                raise InternalServerError from e
        else:
            resp = GetFstabContentsResponse(
                content=(
                    "# Since Backend.AI 20.09, reading the manager fstab is no longer supported."
                ),
                node="manager",
                node_id="manager",
            )
            return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 44. list_mounts (GET /_/mounts)
    # ------------------------------------------------------------------

    async def list_mounts(
        self,
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        root_ctx: RootContext = req.request.app["_root.context"]
        log.info(
            "VFOLDER.LIST_MOUNTS(ak:{})",
            ctx.access_key,
        )
        mount_prefix = await root_ctx.config_provider.legacy_etcd_config_loader.get_raw(
            "volumes/_mount"
        )
        if mount_prefix is None:
            mount_prefix = "/mnt"

        all_volumes = [*await root_ctx.storage_manager.get_all_volumes()]
        all_mounts = [volume_data["path"] for proxy_name, volume_data in all_volumes]
        all_vfolder_hosts = [
            f"{proxy_name}:{volume_data['name']}" for proxy_name, volume_data in all_volumes
        ]

        manager_result = MountResultDTO(
            success=True,
            mounts=all_mounts,
            message="(legacy)",
        )
        storage_proxy_result = MountResultDTO(
            success=True,
            mounts=[list(pair) for pair in zip(all_vfolder_hosts, all_mounts, strict=True)],
            message="",
        )

        async def _fetch_mounts(
            sema: asyncio.Semaphore,
            sess: aiohttp.ClientSession,
            agent_id: str,
        ) -> tuple[str, MountResultDTO]:
            async with sema:
                watcher_info = await get_watcher_info(req.request, agent_id)
                headers = {"X-BackendAI-Watcher-Token": watcher_info["token"]}
                url = watcher_info["addr"] / "mounts"
                try:
                    async with sess.get(url, headers=headers) as watcher_resp:
                        if watcher_resp.status == 200:
                            data = MountResultDTO(
                                success=True,
                                mounts=await watcher_resp.json(),
                                message="",
                            )
                        else:
                            data = MountResultDTO(
                                success=False,
                                mounts=[],
                                message=await watcher_resp.text(),
                            )
                        return (agent_id, data)
                except asyncio.CancelledError:
                    raise
                except TimeoutError:
                    log.error(
                        "VFOLDER.LIST_MOUNTS(u:{}): timeout from watcher (agent:{})",
                        ctx.access_key,
                        agent_id,
                    )
                    raise
                except Exception:
                    log.exception(
                        "VFOLDER.LIST_MOUNTS(u:{}): "
                        "unexpected error while reading from watcher (agent:{})",
                        ctx.access_key,
                        agent_id,
                    )
                    raise

        async with root_ctx.db.begin() as conn:
            db_query = (
                sa.select(agents.c.id)
                .select_from(agents)
                .where(agents.c.status == AgentStatus.ALIVE)
            )
            result = await conn.execute(db_query)
            rows = result.fetchall()

        agents_result: dict[str, MountResultDTO] = {}
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
                        agents_result[mount[0]] = mount[1]

        resp = ListMountsResponse(
            manager=manager_result,
            storage_proxy=storage_proxy_result,
            agents=agents_result,
        )
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 45. mount_host (POST /_/mounts)
    # ------------------------------------------------------------------

    async def mount_host(
        self,
        body: BodyParam[MountHostReq],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        root_ctx: RootContext = req.request.app["_root.context"]
        params = body.parsed
        log_fmt = "VFOLDER.MOUNT_HOST(ak:{}, name:{}, fs:{}, sg:{})"
        log_args = (ctx.access_key, params.name, params.fs_location, params.scaling_group)
        log.info(log_fmt, *log_args)
        mount_prefix = await root_ctx.config_provider.legacy_etcd_config_loader.get_raw(
            "volumes/_mount"
        )
        if mount_prefix is None:
            mount_prefix = "/mnt"

        manager_result = MountResultDTO(
            success=True,
            message="Managers do not have mountpoints since v20.09.",
        )

        async with root_ctx.db.begin() as conn:
            db_query = (
                sa.select(agents.c.id)
                .select_from(agents)
                .where(agents.c.status == AgentStatus.ALIVE)
            )
            if params.scaling_group is not None:
                db_query = db_query.where(agents.c.scaling == params.scaling_group)
            result = await conn.execute(db_query)
            rows = result.fetchall()

        mount_params = {
            "fs_location": params.fs_location,
            "name": params.name,
            "fs_type": params.fs_type,
            "options": params.options,
            "scaling_group": params.scaling_group,
            "fstab_path": params.fstab_path,
            "edit_fstab": params.edit_fstab,
        }

        async def _mount(
            sema: asyncio.Semaphore,
            sess: aiohttp.ClientSession,
            agent_id: str,
        ) -> tuple[str, MountResultDTO]:
            async with sema:
                watcher_info = await get_watcher_info(req.request, agent_id)
                try:
                    headers = {"X-BackendAI-Watcher-Token": watcher_info["token"]}
                    url = watcher_info["addr"] / "mounts"
                    async with sess.post(url, json=mount_params, headers=headers) as resp:
                        if resp.status == 200:
                            data = MountResultDTO(
                                success=True,
                                message=await resp.text(),
                            )
                        else:
                            data = MountResultDTO(
                                success=False,
                                message=await resp.text(),
                            )
                        return (agent_id, data)
                except asyncio.CancelledError:
                    raise
                except TimeoutError:
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

        agents_result: dict[str, MountResultDTO] = {}
        client_timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=client_timeout) as sess:
            sema = asyncio.Semaphore(8)
            mount_results = await asyncio.gather(
                *[_mount(sema, sess, row.id) for row in rows], return_exceptions=True
            )
            for mount_result in mount_results:
                if isinstance(mount_result, BaseException):
                    continue
                agents_result[mount_result[0]] = mount_result[1]

        resp = ListMountsResponse(
            manager=manager_result,
            agents=agents_result,
        )
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 46. umount_host (POST /_/umounts, DELETE /_/mounts)
    # ------------------------------------------------------------------

    async def umount_host(
        self,
        body: BodyParam[UmountHostReq],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        root_ctx: RootContext = req.request.app["_root.context"]
        params = body.parsed
        log_fmt = "VFOLDER.UMOUNT_HOST(ak:{}, name:{}, sg:{})"
        log_args = (ctx.access_key, params.name, params.scaling_group)
        log.info(log_fmt, *log_args)
        mount_prefix = await root_ctx.config_provider.legacy_etcd_config_loader.get_raw(
            "volumes/_mount"
        )
        if mount_prefix is None:
            mount_prefix = "/mnt"
        mountpoint = Path(mount_prefix) / params.name
        if Path(mount_prefix) == mountpoint:
            raise VFolderBadRequest("Mount prefix and mountpoint cannot be the same")

        async with root_ctx.db.begin() as conn, conn.begin():
            db_query = (
                sa.select(kernels.c.mounts)
                .select_from(kernels)
                .where(kernels.c.status != KernelStatus.TERMINATED)
            )
            result = await conn.execute(db_query)
            _kernels = result.fetchall()
            _mounted = set()
            for kern in _kernels:
                if kern.mounts:
                    _mounted.update([m[1] for m in kern.mounts])
            if params.name in _mounted:
                raise VFolderOperationFailed("Target host is used in sessions")

            db_query = (
                sa.select(agents.c.id)
                .select_from(agents)
                .where(agents.c.status == AgentStatus.ALIVE)
            )
            if params.scaling_group is not None:
                db_query = db_query.where(agents.c.scaling == params.scaling_group)
            result = await conn.execute(db_query)
            _agents = result.fetchall()

        manager_result = MountResultDTO(
            success=True,
            message="Managers do not have mountpoints since v20.09.",
        )

        umount_params = {
            "name": params.name,
            "scaling_group": params.scaling_group,
            "fstab_path": params.fstab_path,
            "edit_fstab": params.edit_fstab,
        }

        async def _umount(
            sema: asyncio.Semaphore,
            sess: aiohttp.ClientSession,
            agent_id: str,
        ) -> tuple[str, MountResultDTO]:
            async with sema:
                watcher_info = await get_watcher_info(req.request, agent_id)
                try:
                    headers = {"X-BackendAI-Watcher-Token": watcher_info["token"]}
                    url = watcher_info["addr"] / "mounts"
                    async with sess.delete(url, json=umount_params, headers=headers) as resp:
                        if resp.status == 200:
                            data = MountResultDTO(
                                success=True,
                                message=await resp.text(),
                            )
                        else:
                            data = MountResultDTO(
                                success=False,
                                message=await resp.text(),
                            )
                        return (agent_id, data)
                except asyncio.CancelledError:
                    raise
                except TimeoutError:
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

        agents_result: dict[str, MountResultDTO] = {}
        client_timeout = aiohttp.ClientTimeout(total=10.0)
        async with aiohttp.ClientSession(timeout=client_timeout) as sess:
            sema = asyncio.Semaphore(8)
            umount_results = await asyncio.gather(
                *[_umount(sema, sess, _agent.id) for _agent in _agents], return_exceptions=True
            )
            for umount_result in umount_results:
                if isinstance(umount_result, BaseException):
                    continue
                agents_result[umount_result[0]] = umount_result[1]

        resp = ListMountsResponse(
            manager=manager_result,
            agents=agents_result,
        )
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # 47. change_vfolder_ownership (POST /_/change-ownership)
    # ------------------------------------------------------------------

    async def change_vfolder_ownership(
        self,
        body: BodyParam[ChangeVFolderOwnershipReq],
        ctx: UserContext,
        procs: ProcessorsCtx,
    ) -> APIResponse:
        params = body.parsed
        log.info(
            "VFOLDER.CHANGE_VFOLDER_OWNERSHIP(email:{}, ak:{}, vfid:{}, target:{})",
            ctx.user_email,
            ctx.access_key,
            params.vfolder,
            params.user_email,
        )
        await procs.processors.vfolder.change_vfolder_ownership.wait_for_complete(
            ChangeVFolderOwnershipAction(
                vfolder_id=params.vfolder,
                user_email=params.user_email,
            )
        )
        resp = MessageResponse(msg="")
        return APIResponse.build(HTTPStatus.OK, resp)


# ------------------------------------------------------------------
# Module-level helper used by delete_by_name
# ------------------------------------------------------------------


async def _delete(
    root_ctx: RootContext,
    vfolder_row: Mapping[str, Any],
    user_uuid: uuid.UUID,
    _user_role: UserRole,
    domain_name: str,
    resource_policy: Mapping[str, Any],
) -> None:
    if not vfolder_row["is_owner"]:
        raise InvalidAPIParameters("Cannot delete the vfolder that is not owned by myself.")
    await check_vfolder_status(vfolder_row, VFolderStatusSet.DELETABLE)
    async with root_ctx.db.begin_readonly_session() as db_session:
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
        conn = await db_session.connection()
        await ensure_host_permission_allowed(
            conn,
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
