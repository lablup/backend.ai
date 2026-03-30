"""Tests for ai.backend.common.dto.manager.v2.acl.response module."""

from __future__ import annotations

import json

from ai.backend.common.dto.manager.v2.acl.response import GetPermissionsPayload


class TestGetPermissionsPayload:
    """Tests for GetPermissionsPayload model creation and serialization."""

    def test_creation_with_single_permission(self) -> None:
        payload = GetPermissionsPayload(vfolder_host_permission_list=["create-vfolder"])
        assert payload.vfolder_host_permission_list == ["create-vfolder"]

    def test_creation_with_multiple_permissions(self) -> None:
        permissions = [
            "create-vfolder",
            "modify-vfolder",
            "delete-vfolder",
            "mount-in-session",
            "upload-file",
            "download-file",
            "invite-others",
            "set-user-specific-permission",
        ]
        payload = GetPermissionsPayload(vfolder_host_permission_list=permissions)
        assert len(payload.vfolder_host_permission_list) == 8
        assert "create-vfolder" in payload.vfolder_host_permission_list
        assert "set-user-specific-permission" in payload.vfolder_host_permission_list

    def test_creation_with_empty_list(self) -> None:
        payload = GetPermissionsPayload(vfolder_host_permission_list=[])
        assert payload.vfolder_host_permission_list == []

    def test_creation_from_dict(self) -> None:
        payload = GetPermissionsPayload.model_validate({
            "vfolder_host_permission_list": ["upload-file", "download-file"],
        })
        assert payload.vfolder_host_permission_list == ["upload-file", "download-file"]

    def test_list_is_strings(self) -> None:
        payload = GetPermissionsPayload(
            vfolder_host_permission_list=["create-vfolder", "modify-vfolder"]
        )
        for item in payload.vfolder_host_permission_list:
            assert isinstance(item, str)

    def test_model_dump(self) -> None:
        permissions = ["create-vfolder", "mount-in-session"]
        payload = GetPermissionsPayload(vfolder_host_permission_list=permissions)
        data = payload.model_dump()
        assert data["vfolder_host_permission_list"] == permissions

    def test_model_dump_json(self) -> None:
        permissions = ["upload-file", "download-file"]
        payload = GetPermissionsPayload(vfolder_host_permission_list=permissions)
        json_str = payload.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["vfolder_host_permission_list"] == permissions

    def test_serialization_round_trip(self) -> None:
        permissions = ["create-vfolder", "modify-vfolder", "delete-vfolder"]
        payload = GetPermissionsPayload(vfolder_host_permission_list=permissions)
        json_str = payload.model_dump_json()
        restored = GetPermissionsPayload.model_validate_json(json_str)
        assert restored.vfolder_host_permission_list == permissions

    def test_serialization_round_trip_empty_list(self) -> None:
        payload = GetPermissionsPayload(vfolder_host_permission_list=[])
        json_str = payload.model_dump_json()
        restored = GetPermissionsPayload.model_validate_json(json_str)
        assert restored.vfolder_host_permission_list == []

    def test_json_structure_contains_correct_key(self) -> None:
        payload = GetPermissionsPayload(vfolder_host_permission_list=["create-vfolder"])
        data = json.loads(payload.model_dump_json())
        assert "vfolder_host_permission_list" in data
        assert isinstance(data["vfolder_host_permission_list"], list)

    def test_all_vfolder_host_permissions_accepted(self) -> None:
        all_permissions = [
            "create-vfolder",
            "modify-vfolder",
            "delete-vfolder",
            "mount-in-session",
            "upload-file",
            "download-file",
            "invite-others",
            "set-user-specific-permission",
        ]
        payload = GetPermissionsPayload(vfolder_host_permission_list=all_permissions)
        assert payload.vfolder_host_permission_list == all_permissions
