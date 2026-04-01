"""Tests for ai.backend.common.dto.manager.v2.vfolder.response module."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from ai.backend.common.dto.manager.v2.common import BinarySizeInfo
from ai.backend.common.dto.manager.v2.vfolder.response import (
    CloneVFolderPayload,
    CreateDownloadSessionPayload,
    CreateUploadSessionPayload,
    CreateVFolderPayload,
    DeleteFilesPayload,
    DeleteVFolderPayload,
    FileEntryNode,
    InviteVFolderPayload,
    ListFilesPayload,
    MkdirPayload,
    PurgeVFolderPayload,
    RestoreVFolderPayload,
    ShareVFolderPayload,
    UnshareVFolderPayload,
    UpdateVFolderPayload,
    VFolderCompactNode,
    VFolderInvitationNode,
    VFolderNode,
)
from ai.backend.common.dto.manager.v2.vfolder.types import (
    VFolderAccessControlInfo,
    VFolderInvitationState,
    VFolderMetadataInfo,
    VFolderOperationStatusField,
    VFolderOwnershipInfo,
    VFolderOwnershipTypeField,
    VFolderPermissionField,
    VFolderUsageInfo,
    VFolderUsageMode,
)


def _make_metadata_info() -> VFolderMetadataInfo:
    return VFolderMetadataInfo(
        name="test-folder",
        usage_mode=VFolderUsageMode.GENERAL,
        quota_scope_id="user:abc",
        created_at=datetime.now(tz=UTC),
        last_used=None,
        cloneable=False,
    )


def _make_access_control_info() -> VFolderAccessControlInfo:
    return VFolderAccessControlInfo(
        permission=VFolderPermissionField.READ_WRITE,
        ownership_type=VFolderOwnershipTypeField.USER,
    )


def _make_owner_info() -> VFolderOwnershipInfo:
    return VFolderOwnershipInfo(
        user_id=uuid.uuid4(), project_id=None, creator_email="owner@example.com"
    )


def _make_usage_info() -> VFolderUsageInfo:
    return VFolderUsageInfo(
        num_files=10,
        used_bytes=BinarySizeInfo(value=1024, display="1024"),
        max_size=None,
        max_files=1000,
    )


class TestVFolderNodeCreation:
    """Tests for VFolderNode model creation."""

    def test_creation_with_usage(self) -> None:
        node = VFolderNode(
            id=uuid.uuid4(),
            status=VFolderOperationStatusField.READY,
            host="nfs01",
            metadata=_make_metadata_info(),
            access_control=_make_access_control_info(),
            ownership=_make_owner_info(),
            usage=_make_usage_info(),
        )
        assert node.usage is not None
        assert node.unmanaged_path is None

    def test_creation_without_usage(self) -> None:
        node = VFolderNode(
            id=uuid.uuid4(),
            status=VFolderOperationStatusField.READY,
            host="nfs01",
            metadata=_make_metadata_info(),
            access_control=_make_access_control_info(),
            ownership=_make_owner_info(),
        )
        assert node.usage is None

    def test_round_trip_with_usage(self) -> None:
        node = VFolderNode(
            id=uuid.uuid4(),
            status=VFolderOperationStatusField.READY,
            host="nfs01",
            metadata=_make_metadata_info(),
            access_control=_make_access_control_info(),
            ownership=_make_owner_info(),
            usage=_make_usage_info(),
        )
        restored = VFolderNode.model_validate_json(node.model_dump_json())
        assert restored.metadata.name == node.metadata.name
        assert restored.metadata.cloneable == node.metadata.cloneable
        assert restored.usage is not None
        assert restored.usage.used_bytes.value == 1024

    def test_round_trip_without_usage(self) -> None:
        node = VFolderNode(
            id=uuid.uuid4(),
            status=VFolderOperationStatusField.READY,
            host="nfs01",
            metadata=_make_metadata_info(),
            access_control=_make_access_control_info(),
            ownership=_make_owner_info(),
        )
        restored = VFolderNode.model_validate_json(node.model_dump_json())
        assert restored.usage is None

    def test_nested_structure_in_json(self) -> None:
        node = VFolderNode(
            id=uuid.uuid4(),
            status=VFolderOperationStatusField.READY,
            host="nfs01",
            metadata=_make_metadata_info(),
            access_control=_make_access_control_info(),
            ownership=_make_owner_info(),
        )
        data = json.loads(node.model_dump_json())
        assert "metadata" in data
        assert "access_control" in data
        assert "ownership" in data
        assert "name" in data["metadata"]
        assert "status" in data
        assert "host" in data


class TestVFolderCompactNode:
    """Tests for VFolderCompactNode model."""

    def test_creation(self) -> None:
        vid = uuid.uuid4()
        node = VFolderCompactNode(id=vid, name="compact")
        assert node.id == vid
        assert node.name == "compact"

    def test_round_trip(self) -> None:
        vid = uuid.uuid4()
        node = VFolderCompactNode(id=vid, name="compact")
        restored = VFolderCompactNode.model_validate_json(node.model_dump_json())
        assert restored.id == vid
        assert restored.name == "compact"


class TestVFolderInvitationNode:
    """Tests for VFolderInvitationNode model."""

    def test_creation(self) -> None:
        now = datetime.now(tz=UTC)
        node = VFolderInvitationNode(
            id=uuid.uuid4(),
            vfolder_id=uuid.uuid4(),
            vfolder_name="shared-folder",
            inviter="owner@example.com",
            invitee="guest@example.com",
            permission=VFolderPermissionField.READ_ONLY,
            state=VFolderInvitationState.PENDING,
            created_at=now,
            modified_at=None,
        )
        assert node.state == VFolderInvitationState.PENDING
        assert node.modified_at is None

    def test_round_trip(self) -> None:
        now = datetime.now(tz=UTC)
        node = VFolderInvitationNode(
            id=uuid.uuid4(),
            vfolder_id=uuid.uuid4(),
            vfolder_name="shared",
            inviter="a@b.com",
            invitee="c@d.com",
            permission=VFolderPermissionField.READ_WRITE,
            state=VFolderInvitationState.ACCEPTED,
            created_at=now,
            modified_at=now,
        )
        restored = VFolderInvitationNode.model_validate_json(node.model_dump_json())
        assert restored.state == VFolderInvitationState.ACCEPTED
        assert restored.invitee == "c@d.com"
        assert restored.modified_at is not None


class TestPayloadModels:
    """Tests for Payload models."""

    def test_create_payload(self) -> None:
        node = VFolderNode(
            id=uuid.uuid4(),
            status=VFolderOperationStatusField.READY,
            host="nfs01",
            metadata=_make_metadata_info(),
            access_control=_make_access_control_info(),
            ownership=_make_owner_info(),
        )
        payload = CreateVFolderPayload(vfolder=node)
        assert payload.vfolder.metadata.name == "test-folder"

    def test_update_payload(self) -> None:
        node = VFolderNode(
            id=uuid.uuid4(),
            status=VFolderOperationStatusField.READY,
            host="nfs01",
            metadata=_make_metadata_info(),
            access_control=_make_access_control_info(),
            ownership=_make_owner_info(),
        )
        payload = UpdateVFolderPayload(vfolder=node)
        assert payload.vfolder is not None

    def test_delete_payload(self) -> None:
        vid = uuid.uuid4()
        payload = DeleteVFolderPayload(id=vid)
        assert payload.id == vid

    def test_purge_payload(self) -> None:
        vid = uuid.uuid4()
        payload = PurgeVFolderPayload(id=vid)
        assert payload.id == vid

    def test_restore_payload(self) -> None:
        vid = uuid.uuid4()
        payload = RestoreVFolderPayload(id=vid)
        assert payload.id == vid

    def test_clone_payload(self) -> None:
        node = VFolderNode(
            id=uuid.uuid4(),
            status=VFolderOperationStatusField.READY,
            host="nfs01",
            metadata=_make_metadata_info(),
            access_control=_make_access_control_info(),
            ownership=_make_owner_info(),
        )
        payload = CloneVFolderPayload(vfolder=node, bgtask_id="task-123")
        assert payload.bgtask_id == "task-123"

    def test_mkdir_payload(self) -> None:
        payload = MkdirPayload(results=["/dir1", "/dir2"])
        assert len(payload.results) == 2

    def test_download_session_payload(self) -> None:
        payload = CreateDownloadSessionPayload(token="tok", url="https://example.com/dl")
        assert payload.token == "tok"
        assert "example.com" in payload.url

    def test_upload_session_payload(self) -> None:
        payload = CreateUploadSessionPayload(token="tok", url="https://example.com/ul")
        assert payload.url is not None

    def test_delete_files_payload_none_bgtask(self) -> None:
        payload = DeleteFilesPayload()
        assert payload.bgtask_id is None

    def test_delete_files_payload_with_bgtask(self) -> None:
        payload = DeleteFilesPayload(bgtask_id="task-abc")
        assert payload.bgtask_id == "task-abc"

    def test_list_files_payload(self) -> None:
        entry = FileEntryNode(
            name="file.txt",
            type="file",
            size=100,
            mode="0644",
            created="2024-01-01T00:00:00",
            modified="2024-01-02T00:00:00",
        )
        payload = ListFilesPayload(items=[entry])
        assert len(payload.items) == 1
        assert payload.items[0].name == "file.txt"

    def test_invite_payload(self) -> None:
        payload = InviteVFolderPayload(invited_ids=["inv-1", "inv-2"])
        assert len(payload.invited_ids) == 2

    def test_share_payload(self) -> None:
        payload = ShareVFolderPayload(shared_emails=["a@b.com"])
        assert payload.shared_emails[0] == "a@b.com"

    def test_unshare_payload(self) -> None:
        payload = UnshareVFolderPayload(unshared_emails=["a@b.com"])
        assert payload.unshared_emails[0] == "a@b.com"

    def test_create_payload_round_trip(self) -> None:
        node = VFolderNode(
            id=uuid.uuid4(),
            status=VFolderOperationStatusField.READY,
            host="nfs01",
            metadata=_make_metadata_info(),
            access_control=_make_access_control_info(),
            ownership=_make_owner_info(),
        )
        payload = CreateVFolderPayload(vfolder=node)
        restored = CreateVFolderPayload.model_validate_json(payload.model_dump_json())
        assert restored.vfolder.host == "nfs01"
