"""Tests for VFolder response DTOs."""

import uuid

from ai.backend.common.dto.manager.field import (
    VFolderItemField,
    VFolderOperationStatusField,
    VFolderOwnershipTypeField,
    VFolderPermissionField,
)
from ai.backend.common.dto.manager.vfolder.response import (
    CompactVFolderInfoDTO,
    CreateDownloadSessionResponse,
    CreateUploadSessionResponse,
    GetFstabContentsResponse,
    InviteVFolderResponse,
    ListAllHostsResponse,
    ListAllowedTypesResponse,
    ListInvitationsResponse,
    ListSharedVFoldersResponse,
    MessageResponse,
    MkdirResponse,
    MountResultDTO,
    ShareVFolderResponse,
    UnshareVFolderResponse,
    UpdateQuotaResponse,
    VFolderCloneInfoDTO,
    VFolderCloneResponse,
    VFolderCreatedDTO,
    VFolderCreateResponse,
    VFolderGetIDResponse,
    VFolderGetInfoResponse,
    VFolderInfoDTO,
    VFolderInvitationDTO,
    VFolderListResponse,
    VFolderSharedInfoDTO,
    VolumeInfoDTO,
)
from ai.backend.common.types import VFolderUsageMode


class TestVFolderCreateResponse:
    def test_serialization(self) -> None:
        item = VFolderItemField(
            id="abc123",
            name="test-folder",
            quota_scope_id="qs-1",
            host="host-1",
            usage_mode=VFolderUsageMode.GENERAL,
            created_at="2024-01-01T00:00:00",
            permission=VFolderPermissionField.READ_WRITE,
            max_size=0,
            creator="user@test.com",
            ownership_type=VFolderOwnershipTypeField.USER,
            user="user-uuid",
            group=None,
            cloneable=False,
            status=VFolderOperationStatusField.READY,
            is_owner=True,
            user_email="user@test.com",
            group_name="default",
            type="user",
            max_files=0,
            cur_size=0,
        )
        resp = VFolderCreateResponse(item=item)
        assert resp.item.name == "test-folder"
        assert resp.item.id == "abc123"


class TestVFolderListResponse:
    def test_empty_list(self) -> None:
        resp = VFolderListResponse()
        assert resp.items == []

    def test_with_items(self) -> None:
        item = VFolderItemField(
            id="abc123",
            name="test-folder",
            quota_scope_id="qs-1",
            host="host-1",
            usage_mode=VFolderUsageMode.GENERAL,
            created_at="2024-01-01T00:00:00",
            permission=VFolderPermissionField.READ_WRITE,
            max_size=0,
            creator="user@test.com",
            ownership_type=VFolderOwnershipTypeField.USER,
            user=None,
            group=None,
            cloneable=False,
            status=VFolderOperationStatusField.READY,
            is_owner=True,
            user_email="user@test.com",
            group_name="default",
            type="user",
            max_files=0,
            cur_size=0,
        )
        resp = VFolderListResponse(items=[item])
        assert len(resp.items) == 1


class TestVFolderCreatedDTO:
    def test_serialization(self) -> None:
        dto = VFolderCreatedDTO(
            id="abc123",
            name="test-folder",
            quota_scope_id="qs-1",
            host="host-1",
            usage_mode=VFolderUsageMode.GENERAL,
            permission=VFolderPermissionField.READ_WRITE,
            max_size=0,
            creator="user@test.com",
            ownership_type=VFolderOwnershipTypeField.USER,
            user=None,
            group=None,
            cloneable=False,
            status=VFolderOperationStatusField.READY,
        )
        assert dto.id == "abc123"
        assert dto.unmanaged_path is None


class TestVFolderInfoDTO:
    def test_serialization(self) -> None:
        dto = VFolderInfoDTO(
            name="test-folder",
            id="abc123",
            quota_scope_id="qs-1",
            host="host-1",
            status=VFolderOperationStatusField.READY,
            num_files=10,
            used_bytes=1024,
            created_at="2024-01-01T00:00:00",
            user=None,
            group=None,
            type="user",
            is_owner=True,
            permission=VFolderPermissionField.READ_WRITE,
            usage_mode=VFolderUsageMode.GENERAL,
            cloneable=False,
        )
        assert dto.num_files == 10
        assert dto.used_bytes == 1024
        assert dto.last_used is None


class TestVFolderGetInfoResponse:
    def test_wraps_dto(self) -> None:
        info = VFolderInfoDTO(
            name="test",
            id="abc",
            quota_scope_id="qs-1",
            host="host-1",
            status=VFolderOperationStatusField.READY,
            num_files=0,
            used_bytes=0,
            created_at="2024-01-01",
            user=None,
            group=None,
            type="user",
            is_owner=True,
            permission=VFolderPermissionField.READ_WRITE,
            usage_mode=VFolderUsageMode.GENERAL,
            cloneable=False,
        )
        resp = VFolderGetInfoResponse(item=info)
        assert resp.item.name == "test"


class TestCompactVFolderInfoDTO:
    def test_serialization(self) -> None:
        vid = uuid.uuid4()
        dto = CompactVFolderInfoDTO(id=vid, name="my-folder")
        assert dto.id == vid
        assert dto.name == "my-folder"


class TestVFolderGetIDResponse:
    def test_wraps_dto(self) -> None:
        vid = uuid.uuid4()
        resp = VFolderGetIDResponse(item=CompactVFolderInfoDTO(id=vid, name="test"))
        assert resp.item.id == vid


class TestVFolderInvitationDTO:
    def test_serialization(self) -> None:
        dto = VFolderInvitationDTO(
            id="inv-123",
            inviter="admin@test.com",
            invitee="user@test.com",
            perm=VFolderPermissionField.READ_WRITE,
            state="pending",
            created_at="2024-01-01T00:00:00",
            vfolder_id="vf-123",
            vfolder_name="shared-folder",
        )
        assert dto.id == "inv-123"
        assert dto.modified_at is None


class TestVFolderSharedInfoDTO:
    def test_serialization(self) -> None:
        dto = VFolderSharedInfoDTO(
            vfolder_id="vf-123",
            vfolder_name="shared-folder",
            status="ready",
            owner="owner-uuid",
            type="user",
            shared_to={"uuid": "user-uuid", "email": "user@test.com"},
            perm=VFolderPermissionField.READ_ONLY,
        )
        assert dto.shared_to["email"] == "user@test.com"


class TestVFolderCloneInfoDTO:
    def test_serialization(self) -> None:
        dto = VFolderCloneInfoDTO(
            id="abc",
            name="cloned",
            host="host-1",
            usage_mode=VFolderUsageMode.GENERAL,
            permission=VFolderPermissionField.READ_WRITE,
            creator="user@test.com",
            ownership_type=VFolderOwnershipTypeField.USER,
            user=None,
            group=None,
            cloneable=True,
            bgtask_id="task-123",
        )
        assert dto.bgtask_id == "task-123"


class TestVFolderCloneResponse:
    def test_wraps_dto(self) -> None:
        clone_info = VFolderCloneInfoDTO(
            id="abc",
            name="cloned",
            host="host-1",
            usage_mode=VFolderUsageMode.GENERAL,
            permission=VFolderPermissionField.READ_WRITE,
            creator="user@test.com",
            ownership_type=VFolderOwnershipTypeField.USER,
            user=None,
            group=None,
            cloneable=True,
            bgtask_id="task-123",
        )
        resp = VFolderCloneResponse(item=clone_info)
        assert resp.item.name == "cloned"


class TestFileOperationResponses:
    def test_mkdir_response(self) -> None:
        resp = MkdirResponse(results=["ok", "ok"])
        assert len(resp.results) == 2

    def test_download_session_response(self) -> None:
        resp = CreateDownloadSessionResponse(token="tok-123", url="https://dl.example.com/file")
        assert resp.token == "tok-123"
        assert resp.url.startswith("https://")

    def test_upload_session_response(self) -> None:
        resp = CreateUploadSessionResponse(token="tok-456", url="https://ul.example.com/file")
        assert resp.token == "tok-456"


class TestSharingResponses:
    def test_invite_response(self) -> None:
        resp = InviteVFolderResponse(invited_ids=["uid-1", "uid-2"])
        assert len(resp.invited_ids) == 2

    def test_list_invitations_response(self) -> None:
        resp = ListInvitationsResponse(invitations=[])
        assert resp.invitations == []

    def test_share_response(self) -> None:
        resp = ShareVFolderResponse(shared_emails=["a@test.com"])
        assert resp.shared_emails == ["a@test.com"]

    def test_unshare_response(self) -> None:
        resp = UnshareVFolderResponse(unshared_emails=["a@test.com"])
        assert resp.unshared_emails == ["a@test.com"]

    def test_list_shared_response(self) -> None:
        resp = ListSharedVFoldersResponse(shared=[])
        assert resp.shared == []


class TestAdminResponses:
    def test_list_hosts_response(self) -> None:
        resp = ListAllHostsResponse(default="host-1", allowed=["host-1", "host-2"])
        assert resp.default == "host-1"
        assert len(resp.allowed) == 2

    def test_allowed_types_response(self) -> None:
        resp = ListAllowedTypesResponse(allowed_types=["user", "group"])
        assert "user" in resp.allowed_types

    def test_update_quota_response(self) -> None:
        resp = UpdateQuotaResponse(size_bytes=1024)
        assert resp.size_bytes == 1024

    def test_fstab_contents_response(self) -> None:
        resp = GetFstabContentsResponse(
            content="/dev/sda1 / ext4 defaults 0 1",
            node="manager",
            node_id="manager",
        )
        assert "ext4" in resp.content

    def test_message_response(self) -> None:
        resp = MessageResponse(msg="operation completed")
        assert resp.msg == "operation completed"


class TestVolumeInfoDTO:
    def test_serialization(self) -> None:
        dto = VolumeInfoDTO(
            backend="nfs", capabilities=["read", "write"], usage={"used": 100, "total": 1000}
        )
        assert dto.backend == "nfs"
        assert len(dto.capabilities) == 2


class TestMountResultDTO:
    def test_serialization(self) -> None:
        dto = MountResultDTO(success=True, message="mounted")
        assert dto.success is True
        assert dto.mounts is None
