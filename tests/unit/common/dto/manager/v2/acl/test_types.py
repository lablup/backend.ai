"""Tests for ai.backend.common.dto.manager.v2.acl.types module."""

from __future__ import annotations

import json

from ai.backend.common.dto.manager.v2.acl.types import PermissionListInfo
from ai.backend.common.dto.manager.v2.acl.types import (
    VFolderHostPermission as ExportedVFolderHostPermission,
)
from ai.backend.common.types import VFolderHostPermission


class TestVFolderHostPermissionReExport:
    """Tests verifying VFolderHostPermission is properly re-exported from types module."""

    def test_is_same_object(self) -> None:
        assert ExportedVFolderHostPermission is VFolderHostPermission

    def test_create_value_is_same(self) -> None:
        assert ExportedVFolderHostPermission.CREATE is VFolderHostPermission.CREATE

    def test_all_members_accessible(self) -> None:
        assert ExportedVFolderHostPermission.CREATE.value == "create-vfolder"
        assert ExportedVFolderHostPermission.MODIFY.value == "modify-vfolder"
        assert ExportedVFolderHostPermission.DELETE.value == "delete-vfolder"
        assert ExportedVFolderHostPermission.MOUNT_IN_SESSION.value == "mount-in-session"
        assert ExportedVFolderHostPermission.UPLOAD_FILE.value == "upload-file"
        assert ExportedVFolderHostPermission.DOWNLOAD_FILE.value == "download-file"
        assert ExportedVFolderHostPermission.INVITE_OTHERS.value == "invite-others"
        assert ExportedVFolderHostPermission.SET_USER_PERM.value == "set-user-specific-permission"

    def test_enum_members_count_matches(self) -> None:
        original_count = len(list(VFolderHostPermission))
        exported_count = len(list(ExportedVFolderHostPermission))
        assert original_count == exported_count

    def test_from_string_is_consistent(self) -> None:
        assert ExportedVFolderHostPermission("create-vfolder") is VFolderHostPermission.CREATE


class TestPermissionListInfoCreation:
    """Tests for PermissionListInfo Pydantic model creation."""

    def test_basic_creation_with_single_permission(self) -> None:
        info = PermissionListInfo(vfolder_host_permission_list=["create-vfolder"])
        assert info.vfolder_host_permission_list == ["create-vfolder"]

    def test_creation_with_multiple_permissions(self) -> None:
        permissions = [
            "create-vfolder",
            "modify-vfolder",
            "delete-vfolder",
            "mount-in-session",
        ]
        info = PermissionListInfo(vfolder_host_permission_list=permissions)
        assert len(info.vfolder_host_permission_list) == 4
        assert "create-vfolder" in info.vfolder_host_permission_list
        assert "delete-vfolder" in info.vfolder_host_permission_list

    def test_creation_with_empty_list(self) -> None:
        info = PermissionListInfo(vfolder_host_permission_list=[])
        assert info.vfolder_host_permission_list == []

    def test_creation_from_dict(self) -> None:
        info = PermissionListInfo.model_validate({
            "vfolder_host_permission_list": ["upload-file", "download-file"],
        })
        assert info.vfolder_host_permission_list == ["upload-file", "download-file"]


class TestPermissionListInfoSerialization:
    """Tests for PermissionListInfo serialization and deserialization."""

    def test_model_dump(self) -> None:
        info = PermissionListInfo(
            vfolder_host_permission_list=["create-vfolder", "mount-in-session"]
        )
        data = info.model_dump()
        assert data["vfolder_host_permission_list"] == ["create-vfolder", "mount-in-session"]

    def test_model_dump_json(self) -> None:
        info = PermissionListInfo(vfolder_host_permission_list=["upload-file"])
        json_str = info.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["vfolder_host_permission_list"] == ["upload-file"]

    def test_serialization_round_trip(self) -> None:
        permissions = ["create-vfolder", "modify-vfolder", "delete-vfolder"]
        info = PermissionListInfo(vfolder_host_permission_list=permissions)
        json_str = info.model_dump_json()
        restored = PermissionListInfo.model_validate_json(json_str)
        assert restored.vfolder_host_permission_list == permissions

    def test_serialization_round_trip_empty_list(self) -> None:
        info = PermissionListInfo(vfolder_host_permission_list=[])
        json_str = info.model_dump_json()
        restored = PermissionListInfo.model_validate_json(json_str)
        assert restored.vfolder_host_permission_list == []
