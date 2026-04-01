"""Tests for ai.backend.common.dto.manager.v2.vfolder.request module."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.api_handlers import SENTINEL, Sentinel
from ai.backend.common.dto.manager.v2.vfolder.request import (
    AcceptInvitationInput,
    CloneVFolderInput,
    CreateDownloadSessionInput,
    CreateUploadSessionInput,
    CreateVFolderInput,
    DeleteFilesInput,
    DeleteInvitationInput,
    DeleteVFolderInput,
    InviteVFolderInput,
    ListFilesInput,
    MkdirInput,
    MoveFileInput,
    PurgeVFolderInput,
    RenameFileInput,
    RestoreVFolderInput,
    ShareVFolderInput,
    UnshareVFolderInput,
    UpdateVFolderInput,
)
from ai.backend.common.dto.manager.v2.vfolder.types import VFolderPermissionField, VFolderUsageMode


class TestCreateVFolderInput:
    """Tests for CreateVFolderInput model."""

    def test_valid_creation_with_defaults(self) -> None:
        req = CreateVFolderInput(name="test")
        assert req.name == "test"
        assert req.usage_mode == VFolderUsageMode.GENERAL
        assert req.permission == VFolderPermissionField.READ_WRITE
        assert req.host is None
        assert req.group_id is None
        assert req.cloneable is False
        assert req.unmanaged_path is None

    def test_name_whitespace_stripped(self) -> None:
        req = CreateVFolderInput(name="  test  ")
        assert req.name == "test"

    def test_empty_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateVFolderInput(name="")

    def test_whitespace_only_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateVFolderInput(name="   ")

    def test_valid_with_all_fields(self) -> None:
        gid = uuid.uuid4()
        req = CreateVFolderInput(
            name="my-folder",
            host="nfs01",
            usage_mode=VFolderUsageMode.MODEL,
            permission=VFolderPermissionField.READ_ONLY,
            group_id=gid,
            cloneable=True,
            unmanaged_path="/data/shared",
        )
        assert req.host == "nfs01"
        assert req.usage_mode == VFolderUsageMode.MODEL
        assert req.group_id == gid

    def test_round_trip_serialization(self) -> None:
        req = CreateVFolderInput(name="roundtrip")
        restored = CreateVFolderInput.model_validate_json(req.model_dump_json())
        assert restored.name == "roundtrip"
        assert restored.usage_mode == VFolderUsageMode.GENERAL


class TestUpdateVFolderInput:
    """Tests for UpdateVFolderInput model."""

    def test_default_name_is_sentinel(self) -> None:
        req = UpdateVFolderInput()
        assert req.name is SENTINEL
        assert isinstance(req.name, Sentinel)

    def test_name_none_means_no_change(self) -> None:
        req = UpdateVFolderInput(name=None)
        assert req.name is None

    def test_name_string_update(self) -> None:
        req = UpdateVFolderInput(name="new-name")
        assert req.name == "new-name"

    def test_whitespace_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            UpdateVFolderInput(name="   ")

    def test_cloneable_update(self) -> None:
        req = UpdateVFolderInput(cloneable=True)
        assert req.cloneable is True

    def test_permission_update(self) -> None:
        req = UpdateVFolderInput(permission=VFolderPermissionField.READ_ONLY)
        assert req.permission == VFolderPermissionField.READ_ONLY


class TestDeleteAndRestoreInputs:
    """Tests for DeleteVFolderInput, PurgeVFolderInput, RestoreVFolderInput."""

    def test_delete_valid(self) -> None:
        vid = uuid.uuid4()
        req = DeleteVFolderInput(id=vid)
        assert req.id == vid

    def test_purge_valid(self) -> None:
        vid = uuid.uuid4()
        req = PurgeVFolderInput(id=vid)
        assert req.id == vid

    def test_restore_valid(self) -> None:
        vid = uuid.uuid4()
        req = RestoreVFolderInput(id=vid)
        assert req.id == vid

    def test_invalid_uuid_raises(self) -> None:
        with pytest.raises(ValidationError):
            DeleteVFolderInput.model_validate({"id": "not-a-uuid"})


class TestCloneVFolderInput:
    """Tests for CloneVFolderInput model."""

    def test_valid_creation(self) -> None:
        req = CloneVFolderInput(source_id=uuid.uuid4(), target_name="clone-folder")
        assert req.target_name == "clone-folder"
        assert req.usage_mode == VFolderUsageMode.GENERAL
        assert req.cloneable is False

    def test_target_name_whitespace_stripped(self) -> None:
        req = CloneVFolderInput(source_id=uuid.uuid4(), target_name="  clone  ")
        assert req.target_name == "clone"

    def test_empty_target_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            CloneVFolderInput(source_id=uuid.uuid4(), target_name="")


class TestFileOperationInputs:
    """Tests for file operation input models."""

    def test_mkdir_with_path_string(self) -> None:
        req = MkdirInput(path="/some/dir")
        assert req.path == "/some/dir"
        assert req.parents is True
        assert req.exist_ok is False

    def test_mkdir_with_path_list(self) -> None:
        req = MkdirInput(path=["/a", "/b"])
        assert isinstance(req.path, list)
        assert len(req.path) == 2

    def test_download_session_defaults(self) -> None:
        req = CreateDownloadSessionInput(path="/file.txt")
        assert req.archive is False

    def test_upload_session_size_ge_zero(self) -> None:
        req = CreateUploadSessionInput(path="/upload.bin", size=0)
        assert req.size == 0

    def test_upload_session_negative_size_raises(self) -> None:
        with pytest.raises(ValidationError):
            CreateUploadSessionInput(path="/upload.bin", size=-1)

    def test_rename_file_min_length(self) -> None:
        req = RenameFileInput(target_path="/old.txt", new_name="new.txt")
        assert req.new_name == "new.txt"

    def test_rename_file_empty_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            RenameFileInput(target_path="/old.txt", new_name="")

    def test_move_file(self) -> None:
        req = MoveFileInput(src="/src.txt", dst="/dst.txt")
        assert req.src == "/src.txt"
        assert req.dst == "/dst.txt"

    def test_delete_files_valid(self) -> None:
        req = DeleteFilesInput(files=["/a.txt", "/b.txt"])
        assert len(req.files) == 2
        assert req.recursive is False

    def test_delete_files_empty_list_raises(self) -> None:
        with pytest.raises(ValidationError):
            DeleteFilesInput(files=[])

    def test_list_files_default_path(self) -> None:
        req = ListFilesInput()
        assert req.path == ""


class TestSharingInputs:
    """Tests for sharing/invitation input models."""

    def test_invite_valid(self) -> None:
        req = InviteVFolderInput(emails=["user@example.com"])
        assert req.permission == VFolderPermissionField.READ_WRITE
        assert len(req.emails) == 1

    def test_invite_empty_emails_raises(self) -> None:
        with pytest.raises(ValidationError):
            InviteVFolderInput(emails=[])

    def test_share_valid(self) -> None:
        req = ShareVFolderInput(emails=["a@b.com"])
        assert len(req.emails) == 1

    def test_unshare_valid(self) -> None:
        req = UnshareVFolderInput(emails=["a@b.com"])
        assert len(req.emails) == 1

    def test_accept_invitation(self) -> None:
        inv_id = uuid.uuid4()
        req = AcceptInvitationInput(invitation_id=inv_id)
        assert req.invitation_id == inv_id

    def test_delete_invitation(self) -> None:
        inv_id = uuid.uuid4()
        req = DeleteInvitationInput(invitation_id=inv_id)
        assert req.invitation_id == inv_id
