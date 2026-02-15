from __future__ import annotations

import uuid

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.vfolder import (
    # Request DTOs - Sharing/Invitations
    AcceptInvitationReq,
    # Request DTOs - Admin
    ChangeVFolderOwnershipReq,
    # Request DTOs - CRUD
    CloneVFolderReq,
    # Request DTOs - File Operations
    CreateDownloadSessionReq,
    # Response DTOs
    CreateDownloadSessionResponse,
    CreateUploadSessionReq,
    CreateUploadSessionResponse,
    DeleteFilesAsyncBodyParam,
    DeleteFilesAsyncResponse,
    DeleteFilesReq,
    DeleteInvitationReq,
    DeleteVFolderByIDReq,
    DeleteVFolderFromTrashReq,
    GetFstabContentsQuery,
    GetFstabContentsResponse,
    GetQuotaQuery,
    GetQuotaResponse,
    GetUsageQuery,
    GetUsageResponse,
    GetUsedBytesQuery,
    GetUsedBytesResponse,
    GetVFolderIDReq,
    GetVolumePerfMetricQuery,
    InviteVFolderReq,
    InviteVFolderResponse,
    LeaveVFolderReq,
    ListAllHostsResponse,
    ListAllowedTypesResponse,
    ListFilesQuery,
    ListFilesResponse,
    ListHostsQuery,
    ListHostsResponse,
    ListInvitationsResponse,
    ListMountsResponse,
    ListSentInvitationsResponse,
    # Request DTOs - List/Query
    ListSharedVFoldersQuery,
    ListSharedVFoldersResponse,
    ListVFoldersQuery,
    MessageResponse,
    MkdirReq,
    MkdirResponse,
    MountHostReq,
    MoveFileReq,
    PurgeVFolderReq,
    RenameFileReq,
    RenameVFolderReq,
    RestoreVFolderReq,
    ShareVFolderReq,
    ShareVFolderResponse,
    UmountHostReq,
    UnshareVFolderReq,
    UnshareVFolderResponse,
    UpdateInvitationReq,
    UpdateQuotaReq,
    UpdateQuotaResponse,
    UpdateSharedVFolderReq,
    UpdateVFolderOptionsReq,
    UpdateVFolderSharingStatusReq,
    VFolderCloneResponse,
    VFolderCreateReq,
    VFolderCreateResponse,
    VFolderGetIDResponse,
    VFolderGetInfoResponse,
    VFolderListResponse,
)


class VFolderClient(BaseDomainClient):
    # ============================================================
    # CRUD Operations
    # ============================================================

    async def create(self, request: VFolderCreateReq) -> VFolderCreateResponse:
        return await self._client.typed_request(
            "POST",
            "/folders",
            request=request,
            response_model=VFolderCreateResponse,
        )

    async def list(self, request: ListVFoldersQuery | None = None) -> VFolderListResponse:
        params = (
            {k: str(v) for k, v in request.model_dump(exclude_none=True).items()}
            if request is not None
            else None
        )
        return await self._client.typed_request(
            "GET",
            "/folders",
            params=params,
            response_model=VFolderListResponse,
        )

    async def get_info(self, name: str) -> VFolderGetInfoResponse:
        return await self._client.typed_request(
            "GET",
            f"/folders/{name}",
            response_model=VFolderGetInfoResponse,
        )

    async def get_id(self, request: GetVFolderIDReq) -> VFolderGetIDResponse:
        params = {k: str(v) for k, v in request.model_dump(exclude_none=True).items()}
        return await self._client.typed_request(
            "GET",
            "/folders/_/id",
            params=params,
            response_model=VFolderGetIDResponse,
        )

    async def rename(self, name: str, request: RenameVFolderReq) -> MessageResponse:
        return await self._client.typed_request(
            "POST",
            f"/folders/{name}/rename",
            request=request,
            response_model=MessageResponse,
        )

    async def update_options(self, name: str, request: UpdateVFolderOptionsReq) -> MessageResponse:
        return await self._client.typed_request(
            "POST",
            f"/folders/{name}/update-options",
            request=request,
            response_model=MessageResponse,
        )

    async def delete_by_id(self, request: DeleteVFolderByIDReq) -> MessageResponse:
        return await self._client.typed_request(
            "DELETE",
            "/folders",
            request=request,
            response_model=MessageResponse,
        )

    async def delete_by_name(self, name: str) -> MessageResponse:
        return await self._client.typed_request(
            "DELETE",
            f"/folders/{name}",
            response_model=MessageResponse,
        )

    async def clone(self, name: str, request: CloneVFolderReq) -> VFolderCloneResponse:
        return await self._client.typed_request(
            "POST",
            f"/folders/{name}/clone",
            request=request,
            response_model=VFolderCloneResponse,
        )

    async def purge(self, request: PurgeVFolderReq) -> MessageResponse:
        return await self._client.typed_request(
            "POST",
            "/folders/purge",
            request=request,
            response_model=MessageResponse,
        )

    async def restore(self, request: RestoreVFolderReq) -> MessageResponse:
        return await self._client.typed_request(
            "POST",
            "/folders/restore-from-trash-bin",
            request=request,
            response_model=MessageResponse,
        )

    async def delete_from_trash(self, request: DeleteVFolderFromTrashReq) -> MessageResponse:
        return await self._client.typed_request(
            "POST",
            "/folders/delete-from-trash-bin",
            request=request,
            response_model=MessageResponse,
        )

    async def force_delete(self, folder_id: uuid.UUID) -> MessageResponse:
        return await self._client.typed_request(
            "DELETE",
            f"/folders/{folder_id}/force",
            response_model=MessageResponse,
        )

    # ============================================================
    # File Operations
    # ============================================================

    async def mkdir(self, name: str, request: MkdirReq) -> MkdirResponse:
        return await self._client.typed_request(
            "POST",
            f"/folders/{name}/mkdir",
            request=request,
            response_model=MkdirResponse,
        )

    async def create_download_session(
        self, name: str, request: CreateDownloadSessionReq
    ) -> CreateDownloadSessionResponse:
        return await self._client.typed_request(
            "POST",
            f"/folders/{name}/request-download",
            request=request,
            response_model=CreateDownloadSessionResponse,
        )

    async def create_upload_session(
        self, name: str, request: CreateUploadSessionReq
    ) -> CreateUploadSessionResponse:
        return await self._client.typed_request(
            "POST",
            f"/folders/{name}/request-upload",
            request=request,
            response_model=CreateUploadSessionResponse,
        )

    async def list_files(
        self, name: str, request: ListFilesQuery | None = None
    ) -> ListFilesResponse:
        params = (
            {k: str(v) for k, v in request.model_dump(exclude_none=True).items()}
            if request is not None
            else None
        )
        return await self._client.typed_request(
            "GET",
            f"/folders/{name}/files",
            params=params,
            response_model=ListFilesResponse,
        )

    async def rename_file(self, name: str, request: RenameFileReq) -> MessageResponse:
        return await self._client.typed_request(
            "POST",
            f"/folders/{name}/rename-file",
            request=request,
            response_model=MessageResponse,
        )

    async def move_file(self, name: str, request: MoveFileReq) -> MessageResponse:
        return await self._client.typed_request(
            "POST",
            f"/folders/{name}/move-file",
            request=request,
            response_model=MessageResponse,
        )

    async def delete_files(self, name: str, request: DeleteFilesReq) -> MessageResponse:
        return await self._client.typed_request(
            "POST",
            f"/folders/{name}/delete-files",
            request=request,
            response_model=MessageResponse,
        )

    async def delete_files_async(
        self, name: str, request: DeleteFilesAsyncBodyParam
    ) -> DeleteFilesAsyncResponse:
        return await self._client.typed_request(
            "POST",
            f"/folders/{name}/delete-files-async",
            request=request,
            response_model=DeleteFilesAsyncResponse,
        )

    # ============================================================
    # Sharing/Invitation Operations
    # ============================================================

    async def invite(self, name: str, request: InviteVFolderReq) -> InviteVFolderResponse:
        return await self._client.typed_request(
            "POST",
            f"/folders/{name}/invite",
            request=request,
            response_model=InviteVFolderResponse,
        )

    async def share(self, name: str, request: ShareVFolderReq) -> ShareVFolderResponse:
        return await self._client.typed_request(
            "POST",
            f"/folders/{name}/share",
            request=request,
            response_model=ShareVFolderResponse,
        )

    async def unshare(self, name: str, request: UnshareVFolderReq) -> UnshareVFolderResponse:
        return await self._client.typed_request(
            "POST",
            f"/folders/{name}/unshare",
            request=request,
            response_model=UnshareVFolderResponse,
        )

    async def leave(self, name: str, request: LeaveVFolderReq | None = None) -> MessageResponse:
        return await self._client.typed_request(
            "POST",
            f"/folders/{name}/leave",
            request=request,
            response_model=MessageResponse,
        )

    async def list_invitations(self) -> ListInvitationsResponse:
        return await self._client.typed_request(
            "GET",
            "/folders/invitations/list",
            response_model=ListInvitationsResponse,
        )

    async def list_sent_invitations(self) -> ListSentInvitationsResponse:
        return await self._client.typed_request(
            "GET",
            "/folders/invitations/list-sent",
            response_model=ListSentInvitationsResponse,
        )

    async def accept_invitation(self, request: AcceptInvitationReq) -> MessageResponse:
        return await self._client.typed_request(
            "POST",
            "/folders/invitations/accept",
            request=request,
            response_model=MessageResponse,
        )

    async def delete_invitation(self, request: DeleteInvitationReq) -> MessageResponse:
        return await self._client.typed_request(
            "POST",
            "/folders/invitations/delete",
            request=request,
            response_model=MessageResponse,
        )

    async def update_invitation(self, inv_id: str, request: UpdateInvitationReq) -> MessageResponse:
        return await self._client.typed_request(
            "POST",
            f"/folders/invitations/update/{inv_id}",
            request=request,
            response_model=MessageResponse,
        )

    async def list_shared(
        self, request: ListSharedVFoldersQuery | None = None
    ) -> ListSharedVFoldersResponse:
        params = (
            {k: str(v) for k, v in request.model_dump(exclude_none=True).items()}
            if request is not None
            else None
        )
        return await self._client.typed_request(
            "GET",
            "/folders/_/shared",
            params=params,
            response_model=ListSharedVFoldersResponse,
        )

    async def update_shared(self, request: UpdateSharedVFolderReq) -> MessageResponse:
        return await self._client.typed_request(
            "POST",
            "/folders/_/shared",
            request=request,
            response_model=MessageResponse,
        )

    async def update_sharing_status(
        self, request: UpdateVFolderSharingStatusReq
    ) -> MessageResponse:
        return await self._client.typed_request(
            "POST",
            "/folders/_/sharing",
            request=request,
            response_model=MessageResponse,
        )

    # ============================================================
    # Admin/Host Operations
    # ============================================================

    async def list_hosts(self, request: ListHostsQuery | None = None) -> ListHostsResponse:
        params = (
            {k: str(v) for k, v in request.model_dump(exclude_none=True).items()}
            if request is not None
            else None
        )
        return await self._client.typed_request(
            "GET",
            "/folders/_/hosts",
            params=params,
            response_model=ListHostsResponse,
        )

    async def list_all_hosts(self) -> ListAllHostsResponse:
        return await self._client.typed_request(
            "GET",
            "/folders/_/all-hosts",
            response_model=ListAllHostsResponse,
        )

    async def list_allowed_types(self) -> ListAllowedTypesResponse:
        return await self._client.typed_request(
            "GET",
            "/folders/_/allowed-types",
            response_model=ListAllowedTypesResponse,
        )

    async def get_volume_perf_metric(self, request: GetVolumePerfMetricQuery) -> GetQuotaResponse:
        params = {k: str(v) for k, v in request.model_dump(exclude_none=True).items()}
        return await self._client.typed_request(
            "GET",
            "/folders/_/perf-metric",
            params=params,
            response_model=GetQuotaResponse,
        )

    async def get_quota(self, request: GetQuotaQuery) -> GetQuotaResponse:
        params = {k: str(v) for k, v in request.model_dump(exclude_none=True).items()}
        return await self._client.typed_request(
            "GET",
            "/folders/_/quota",
            params=params,
            response_model=GetQuotaResponse,
        )

    async def update_quota(self, request: UpdateQuotaReq) -> UpdateQuotaResponse:
        return await self._client.typed_request(
            "POST",
            "/folders/_/quota",
            request=request,
            response_model=UpdateQuotaResponse,
        )

    async def get_usage(self, request: GetUsageQuery) -> GetUsageResponse:
        params = {k: str(v) for k, v in request.model_dump(exclude_none=True).items()}
        return await self._client.typed_request(
            "GET",
            "/folders/_/usage",
            params=params,
            response_model=GetUsageResponse,
        )

    async def get_used_bytes(self, request: GetUsedBytesQuery) -> GetUsedBytesResponse:
        params = {k: str(v) for k, v in request.model_dump(exclude_none=True).items()}
        return await self._client.typed_request(
            "GET",
            "/folders/_/used-bytes",
            params=params,
            response_model=GetUsedBytesResponse,
        )

    async def get_fstab_contents(
        self, request: GetFstabContentsQuery | None = None
    ) -> GetFstabContentsResponse:
        params = (
            {k: str(v) for k, v in request.model_dump(exclude_none=True).items()}
            if request is not None
            else None
        )
        return await self._client.typed_request(
            "GET",
            "/folders/_/fstab",
            params=params,
            response_model=GetFstabContentsResponse,
        )

    async def list_mounts(self) -> ListMountsResponse:
        return await self._client.typed_request(
            "GET",
            "/folders/_/mounts",
            response_model=ListMountsResponse,
        )

    async def mount_host(self, request: MountHostReq) -> ListMountsResponse:
        return await self._client.typed_request(
            "POST",
            "/folders/_/mounts",
            request=request,
            response_model=ListMountsResponse,
        )

    async def umount_host(self, request: UmountHostReq) -> ListMountsResponse:
        return await self._client.typed_request(
            "POST",
            "/folders/_/umounts",
            request=request,
            response_model=ListMountsResponse,
        )

    async def change_ownership(self, request: ChangeVFolderOwnershipReq) -> MessageResponse:
        return await self._client.typed_request(
            "POST",
            "/folders/_/change-ownership",
            request=request,
            response_model=MessageResponse,
        )
