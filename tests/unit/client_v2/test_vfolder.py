from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.vfolder import VFolderClient
from ai.backend.common.dto.manager.field import VFolderPermissionField
from ai.backend.common.dto.manager.vfolder import (
    AcceptInvitationReq,
    ChangeVFolderOwnershipReq,
    CloneVFolderReq,
    CreateDownloadSessionReq,
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
    ListAllHostsResponse,
    ListAllowedTypesResponse,
    ListFilesQuery,
    ListFilesResponse,
    ListHostsResponse,
    ListInvitationsResponse,
    ListMountsResponse,
    ListSentInvitationsResponse,
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
    UserPermMapping,
    VFolderCloneResponse,
    VFolderCreateReq,
    VFolderCreateResponse,
    VFolderGetIDResponse,
    VFolderGetInfoResponse,
    VFolderListResponse,
)

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))


def _make_client(
    mock_session: MagicMock | None = None,
    config: ClientConfig | None = None,
) -> BackendAIClient:
    return BackendAIClient(
        config or _DEFAULT_CONFIG,
        MockAuth(),
        mock_session or MagicMock(),
    )


def _make_request_session(resp: AsyncMock) -> MagicMock:
    """Build a mock session whose ``request()`` returns *resp* as a context manager."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


def _make_vfolder_client(mock_session: MagicMock) -> VFolderClient:
    client = _make_client(mock_session)
    return VFolderClient(client)


def _mock_json_response(data: dict[str, Any], status: int = 200) -> AsyncMock:
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=data)
    return resp


# ============================================================
# CRUD Tests
# ============================================================


class TestVFolderCRUD:
    @pytest.mark.asyncio
    async def test_create(self) -> None:
        response_data = {
            "item": {
                "id": "abc123",
                "name": "my-folder",
                "quota_scope_id": "qs-1",
                "host": "local:volume1",
                "usage_mode": "general",
                "permission": "rw",
                "max_size": 0,
                "creator": "user@test.com",
                "ownership_type": "user",
                "cloneable": False,
                "status": "ready",
                "created_at": "2025-01-01T00:00:00",
                "is_owner": True,
                "user_email": "user@test.com",
                "group_name": "default",
                "type": "user",
                "max_files": 0,
                "cur_size": 0,
                "user": None,
                "group": None,
            }
        }
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.create(VFolderCreateReq(name="my-folder"))

        assert isinstance(result, VFolderCreateResponse)
        assert result.item.name == "my-folder"

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1].endswith("/folders")
        assert call_args.kwargs["json"]["name"] == "my-folder"

    @pytest.mark.asyncio
    async def test_list(self) -> None:
        response_data: dict[str, Any] = {"items": []}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.list()

        assert isinstance(result, VFolderListResponse)
        assert result.items == []

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1].endswith("/folders")

    @pytest.mark.asyncio
    async def test_list_with_query(self) -> None:
        response_data: dict[str, Any] = {"items": []}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.list(ListVFoldersQuery(all=True))

        assert isinstance(result, VFolderListResponse)
        call_args = mock_session.request.call_args
        assert call_args.kwargs["params"]["all"] == "True"

    @pytest.mark.asyncio
    async def test_get_info(self) -> None:
        response_data = {
            "item": {
                "name": "test-folder",
                "id": "abc123",
                "quota_scope_id": "qs-1",
                "host": "local:vol",
                "status": "ready",
                "num_files": 10,
                "used_bytes": 1024,
                "created_at": "2025-01-01T00:00:00",
                "type": "user",
                "is_owner": True,
                "permission": "rw",
                "usage_mode": "general",
                "cloneable": False,
            }
        }
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.get_info("test-folder")

        assert isinstance(result, VFolderGetInfoResponse)
        assert result.item.name == "test-folder"

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/folders/test-folder" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_id(self) -> None:
        folder_id = uuid.uuid4()
        response_data = {"item": {"id": str(folder_id), "name": "my-folder"}}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.get_id(GetVFolderIDReq(name="my-folder"))

        assert isinstance(result, VFolderGetIDResponse)
        assert result.item.name == "my-folder"

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/folders/_/id" in call_args[0][1]
        assert call_args.kwargs["params"]["name"] == "my-folder"

    @pytest.mark.asyncio
    async def test_rename(self) -> None:
        response_data = {"msg": "renamed"}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.rename("old-name", RenameVFolderReq(new_name="new-name"))

        assert isinstance(result, MessageResponse)
        assert result.msg == "renamed"

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/folders/old-name/rename" in call_args[0][1]
        assert call_args.kwargs["json"]["new_name"] == "new-name"

    @pytest.mark.asyncio
    async def test_update_options(self) -> None:
        response_data = {"msg": "updated"}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.update_options("my-folder", UpdateVFolderOptionsReq(cloneable=True))

        assert isinstance(result, MessageResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/folders/my-folder/update-options" in call_args[0][1]
        assert call_args.kwargs["json"]["cloneable"] is True

    @pytest.mark.asyncio
    async def test_delete_by_id(self) -> None:
        folder_id = uuid.uuid4()
        response_data = {"msg": "deleted"}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.delete_by_id(DeleteVFolderByIDReq(vfolder_id=folder_id))

        assert isinstance(result, MessageResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "DELETE"
        assert call_args[0][1].endswith("/folders")
        assert str(call_args.kwargs["json"]["vfolder_id"]) == str(folder_id)

    @pytest.mark.asyncio
    async def test_delete_by_name(self) -> None:
        response_data = {"msg": "deleted"}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.delete_by_name("my-folder")

        assert isinstance(result, MessageResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "DELETE"
        assert "/folders/my-folder" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_clone(self) -> None:
        response_data = {
            "item": {
                "id": "clone-id",
                "name": "cloned-folder",
                "host": "local:vol",
                "usage_mode": "general",
                "permission": "rw",
                "creator": "user@test.com",
                "ownership_type": "user",
                "cloneable": False,
                "bgtask_id": "task-123",
            }
        }
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.clone("original", CloneVFolderReq(target_name="cloned-folder"))

        assert isinstance(result, VFolderCloneResponse)
        assert result.item.name == "cloned-folder"

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/folders/original/clone" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_purge(self) -> None:
        folder_id = uuid.uuid4()
        response_data = {"msg": "purged"}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.purge(PurgeVFolderReq(vfolder_id=folder_id))

        assert isinstance(result, MessageResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/folders/purge" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_restore(self) -> None:
        folder_id = uuid.uuid4()
        response_data = {"msg": "restored"}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.restore(RestoreVFolderReq(vfolder_id=folder_id))

        assert isinstance(result, MessageResponse)
        call_args = mock_session.request.call_args
        assert "/folders/restore-from-trash-bin" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_delete_from_trash(self) -> None:
        folder_id = uuid.uuid4()
        response_data = {"msg": "deleted from trash"}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.delete_from_trash(DeleteVFolderFromTrashReq(vfolder_id=folder_id))

        assert isinstance(result, MessageResponse)
        call_args = mock_session.request.call_args
        assert "/folders/delete-from-trash-bin" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_force_delete(self) -> None:
        folder_id = uuid.uuid4()
        response_data = {"msg": "force deleted"}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.force_delete(folder_id)

        assert isinstance(result, MessageResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "DELETE"
        assert f"/folders/{folder_id}/force" in call_args[0][1]


# ============================================================
# File Operation Tests
# ============================================================


class TestVFolderFileOps:
    @pytest.mark.asyncio
    async def test_mkdir(self) -> None:
        response_data: dict[str, Any] = {"results": []}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.mkdir("my-folder", MkdirReq(path="subdir"))

        assert isinstance(result, MkdirResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/folders/my-folder/mkdir" in call_args[0][1]
        assert call_args.kwargs["json"]["path"] == "subdir"

    @pytest.mark.asyncio
    async def test_create_download_session(self) -> None:
        response_data = {"token": "dl-token", "url": "https://storage/download"}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.create_download_session(
            "my-folder", CreateDownloadSessionReq(path="file.txt")
        )

        assert isinstance(result, CreateDownloadSessionResponse)
        assert result.token == "dl-token"
        call_args = mock_session.request.call_args
        assert "/folders/my-folder/request-download" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_create_upload_session(self) -> None:
        response_data = {"token": "ul-token", "url": "https://storage/upload"}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.create_upload_session(
            "my-folder", CreateUploadSessionReq(path="file.txt", size=1024)
        )

        assert isinstance(result, CreateUploadSessionResponse)
        assert result.token == "ul-token"
        call_args = mock_session.request.call_args
        assert "/folders/my-folder/request-upload" in call_args[0][1]
        assert call_args.kwargs["json"]["size"] == 1024

    @pytest.mark.asyncio
    async def test_list_files(self) -> None:
        response_data = {"items": [{"name": "test.txt"}]}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.list_files("my-folder", ListFilesQuery(path="subdir"))

        assert isinstance(result, ListFilesResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/folders/my-folder/files" in call_args[0][1]
        assert call_args.kwargs["params"]["path"] == "subdir"

    @pytest.mark.asyncio
    async def test_rename_file(self) -> None:
        response_data = {"msg": "renamed"}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.rename_file(
            "my-folder", RenameFileReq(target_path="old.txt", new_name="new.txt")
        )

        assert isinstance(result, MessageResponse)
        call_args = mock_session.request.call_args
        assert "/folders/my-folder/rename-file" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_move_file(self) -> None:
        response_data = {"msg": "moved"}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.move_file("my-folder", MoveFileReq(src="a.txt", dst="b/a.txt"))

        assert isinstance(result, MessageResponse)
        call_args = mock_session.request.call_args
        assert "/folders/my-folder/move-file" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_delete_files(self) -> None:
        response_data = {"msg": "deleted"}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.delete_files("my-folder", DeleteFilesReq(files=["a.txt", "b.txt"]))

        assert isinstance(result, MessageResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/folders/my-folder/delete-files" in call_args[0][1]
        assert call_args.kwargs["json"]["files"] == ["a.txt", "b.txt"]

    @pytest.mark.asyncio
    async def test_delete_files_async(self) -> None:
        response_data = {"bgtask_id": "12345678-1234-5678-1234-567812345678"}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.delete_files_async(
            "my-folder", DeleteFilesAsyncBodyParam(files=["c.txt"], recursive=True)
        )

        assert isinstance(result, DeleteFilesAsyncResponse)
        call_args = mock_session.request.call_args
        assert "/folders/my-folder/delete-files-async" in call_args[0][1]


# ============================================================
# Sharing/Invitation Tests
# ============================================================


class TestVFolderSharing:
    @pytest.mark.asyncio
    async def test_invite(self) -> None:
        response_data = {"invited_ids": ["user-1", "user-2"]}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.invite(
            "my-folder",
            InviteVFolderReq(emails=["a@test.com", "b@test.com"]),
        )

        assert isinstance(result, InviteVFolderResponse)
        assert len(result.invited_ids) == 2
        call_args = mock_session.request.call_args
        assert "/folders/my-folder/invite" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_share(self) -> None:
        response_data = {"shared_emails": ["a@test.com"]}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.share("my-folder", ShareVFolderReq(emails=["a@test.com"]))

        assert isinstance(result, ShareVFolderResponse)
        call_args = mock_session.request.call_args
        assert "/folders/my-folder/share" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_unshare(self) -> None:
        response_data = {"unshared_emails": ["a@test.com"]}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.unshare("my-folder", UnshareVFolderReq(emails=["a@test.com"]))

        assert isinstance(result, UnshareVFolderResponse)
        call_args = mock_session.request.call_args
        assert "/folders/my-folder/unshare" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_leave(self) -> None:
        response_data = {"msg": "left"}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.leave("my-folder")

        assert isinstance(result, MessageResponse)
        call_args = mock_session.request.call_args
        assert "/folders/my-folder/leave" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_list_invitations(self) -> None:
        response_data: dict[str, Any] = {"invitations": []}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.list_invitations()

        assert isinstance(result, ListInvitationsResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/folders/invitations/list" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_list_sent_invitations(self) -> None:
        response_data: dict[str, Any] = {"invitations": []}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.list_sent_invitations()

        assert isinstance(result, ListSentInvitationsResponse)
        call_args = mock_session.request.call_args
        assert "/folders/invitations/list-sent" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_accept_invitation(self) -> None:
        response_data = {"msg": "accepted"}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.accept_invitation(AcceptInvitationReq(inv_id="inv-1"))

        assert isinstance(result, MessageResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/folders/invitations/accept" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_delete_invitation(self) -> None:
        response_data = {"msg": "deleted"}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.delete_invitation(DeleteInvitationReq(inv_id="inv-1"))

        assert isinstance(result, MessageResponse)
        call_args = mock_session.request.call_args
        assert "/folders/invitations/delete" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_update_invitation(self) -> None:
        response_data = {"msg": "updated"}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.update_invitation(
            "inv-1",
            UpdateInvitationReq(permission=VFolderPermissionField.READ_ONLY),
        )

        assert isinstance(result, MessageResponse)
        call_args = mock_session.request.call_args
        assert "/folders/invitations/update/inv-1" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_list_shared(self) -> None:
        response_data: dict[str, Any] = {"shared": []}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.list_shared()

        assert isinstance(result, ListSharedVFoldersResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/folders/_/shared" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_update_shared(self) -> None:
        response_data = {"msg": "updated"}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()
        result = await vfolder.update_shared(
            UpdateSharedVFolderReq(
                vfolder=vfolder_id,
                user=user_id,
                permission=VFolderPermissionField.READ_ONLY,
            )
        )

        assert isinstance(result, MessageResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/folders/_/shared" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_update_sharing_status(self) -> None:
        response_data = {"msg": "updated"}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()
        result = await vfolder.update_sharing_status(
            UpdateVFolderSharingStatusReq(
                vfolder_id=vfolder_id,
                user_perm_list=[
                    UserPermMapping(
                        user_id=user_id,
                        perm=VFolderPermissionField.READ_WRITE,
                    )
                ],
            )
        )

        assert isinstance(result, MessageResponse)
        call_args = mock_session.request.call_args
        assert "/folders/_/sharing" in call_args[0][1]


# ============================================================
# Admin/Host Tests
# ============================================================


class TestVFolderAdmin:
    @pytest.mark.asyncio
    async def test_list_hosts(self) -> None:
        response_data = {"default": "local:vol", "allowed": ["local:vol"], "volume_info": {}}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.list_hosts()

        assert isinstance(result, ListHostsResponse)
        assert result.default == "local:vol"
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/folders/_/hosts" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_list_all_hosts(self) -> None:
        response_data = {"default": "local:vol", "allowed": ["local:vol"]}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.list_all_hosts()

        assert isinstance(result, ListAllHostsResponse)
        call_args = mock_session.request.call_args
        assert "/folders/_/all-hosts" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_list_allowed_types(self) -> None:
        response_data = {"allowed_types": ["user", "group"]}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.list_allowed_types()

        assert isinstance(result, ListAllowedTypesResponse)
        assert result.allowed_types == ["user", "group"]

    @pytest.mark.asyncio
    async def test_get_quota(self) -> None:
        quota_id = uuid.uuid4()
        response_data = {"data": {"used_bytes": 1024, "limit_bytes": 10240}}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.get_quota(GetQuotaQuery(folder_host="local:vol", id=quota_id))

        assert isinstance(result, GetQuotaResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/folders/_/quota" in call_args[0][1]
        assert call_args.kwargs["params"]["folder_host"] == "local:vol"

    @pytest.mark.asyncio
    async def test_update_quota(self) -> None:
        quota_id = uuid.uuid4()
        response_data = {"size_bytes": 20480}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.update_quota(
            UpdateQuotaReq(
                folder_host="local:vol",
                id=quota_id,
                input={"size_bytes": 20480},
            )
        )

        assert isinstance(result, UpdateQuotaResponse)
        assert result.size_bytes == 20480
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/folders/_/quota" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_volume_perf_metric(self) -> None:
        response_data = {"data": {"iops_read": 100}}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.get_volume_perf_metric(
            GetVolumePerfMetricQuery(folder_host="local:vol")
        )

        assert isinstance(result, GetQuotaResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/folders/_/perf-metric" in call_args[0][1]
        assert call_args.kwargs["params"]["folder_host"] == "local:vol"

    @pytest.mark.asyncio
    async def test_get_usage(self) -> None:
        quota_id = uuid.uuid4()
        response_data = {"data": {"used_bytes": 512}}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.get_usage(GetUsageQuery(folder_host="local:vol", id=quota_id))

        assert isinstance(result, GetUsageResponse)
        call_args = mock_session.request.call_args
        assert "/folders/_/usage" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_used_bytes(self) -> None:
        quota_id = uuid.uuid4()
        response_data = {"data": {"used_bytes": 256}}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.get_used_bytes(
            GetUsedBytesQuery(folder_host="local:vol", id=quota_id)
        )

        assert isinstance(result, GetUsedBytesResponse)
        call_args = mock_session.request.call_args
        assert "/folders/_/used-bytes" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_fstab_contents(self) -> None:
        response_data = {"content": "nfs data", "node": "manager", "node_id": "mgr-1"}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.get_fstab_contents(GetFstabContentsQuery(fstab_path="/etc/fstab"))

        assert isinstance(result, GetFstabContentsResponse)
        assert result.content == "nfs data"
        call_args = mock_session.request.call_args
        assert "/folders/_/fstab" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_list_mounts(self) -> None:
        response_data = {
            "manager": {"success": True, "message": "ok"},
            "agents": {},
        }
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.list_mounts()

        assert isinstance(result, ListMountsResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/folders/_/mounts" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_mount_host(self) -> None:
        response_data = {
            "manager": {"success": True, "message": "mounted"},
            "agents": {},
        }
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.mount_host(MountHostReq(fs_location="/mnt/nfs", name="nfs-share"))

        assert isinstance(result, ListMountsResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/folders/_/mounts" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_umount_host(self) -> None:
        response_data = {
            "manager": {"success": True, "message": "unmounted"},
            "agents": {},
        }
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.umount_host(UmountHostReq(name="nfs-share"))

        assert isinstance(result, ListMountsResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/folders/_/umounts" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_change_ownership(self) -> None:
        vfolder_id = uuid.uuid4()
        response_data = {"msg": "ownership changed"}
        mock_session = _make_request_session(_mock_json_response(response_data))
        vfolder = _make_vfolder_client(mock_session)

        result = await vfolder.change_ownership(
            ChangeVFolderOwnershipReq(vfolder=vfolder_id, user_email="new-owner@test.com")
        )

        assert isinstance(result, MessageResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/folders/_/change-ownership" in call_args[0][1]
