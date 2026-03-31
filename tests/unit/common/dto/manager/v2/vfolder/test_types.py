"""Tests for ai.backend.common.dto.manager.v2.vfolder.types module."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from ai.backend.common.dto.manager.v2.common import BinarySizeInfo
from ai.backend.common.dto.manager.v2.vfolder.types import (
    OrderDirection,
    VFolderAccessControlInfo,
    VFolderInvitationState,
    VFolderMetadataInfo,
    VFolderOperationStatusField,
    VFolderOrderField,
    VFolderOwnershipInfo,
    VFolderOwnershipTypeField,
    VFolderPermissionField,
    VFolderUsageInfo,
    VFolderUsageMode,
)


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "ASC"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "DESC"

    def test_enum_members_count(self) -> None:
        assert len(list(OrderDirection)) == 2

    def test_from_string_asc(self) -> None:
        assert OrderDirection("ASC") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("DESC") is OrderDirection.DESC


class TestVFolderOrderField:
    """Tests for VFolderOrderField enum."""

    def test_name_value(self) -> None:
        assert VFolderOrderField.NAME.value == "name"

    def test_created_at_value(self) -> None:
        assert VFolderOrderField.CREATED_AT.value == "created_at"

    def test_status_value(self) -> None:
        assert VFolderOrderField.STATUS.value == "status"

    def test_usage_mode_value(self) -> None:
        assert VFolderOrderField.USAGE_MODE.value == "usage_mode"

    def test_host_value(self) -> None:
        assert VFolderOrderField.HOST.value == "host"

    def test_enum_members_count(self) -> None:
        assert len(list(VFolderOrderField)) == 5


class TestVFolderInvitationState:
    """Tests for VFolderInvitationState enum."""

    def test_pending_value(self) -> None:
        assert VFolderInvitationState.PENDING.value == "pending"

    def test_canceled_value(self) -> None:
        assert VFolderInvitationState.CANCELED.value == "canceled"

    def test_accepted_value(self) -> None:
        assert VFolderInvitationState.ACCEPTED.value == "accepted"

    def test_rejected_value(self) -> None:
        assert VFolderInvitationState.REJECTED.value == "rejected"

    def test_enum_members_count(self) -> None:
        assert len(list(VFolderInvitationState)) == 4


class TestReExportedEnums:
    """Tests verifying that enums are properly re-exported."""

    def test_vfolder_permission_field_read_write(self) -> None:
        assert VFolderPermissionField.READ_WRITE.value == "rw"

    def test_vfolder_permission_field_read_only(self) -> None:
        assert VFolderPermissionField.READ_ONLY.value == "ro"

    def test_vfolder_operation_status_ready(self) -> None:
        assert VFolderOperationStatusField.READY.value == "ready"

    def test_vfolder_ownership_type_user(self) -> None:
        assert VFolderOwnershipTypeField.USER.value == "user"

    def test_vfolder_ownership_type_group(self) -> None:
        assert VFolderOwnershipTypeField.GROUP.value == "group"

    def test_vfolder_usage_mode_general(self) -> None:
        assert VFolderUsageMode.GENERAL.value == "general"

    def test_vfolder_usage_mode_model(self) -> None:
        assert VFolderUsageMode.MODEL.value == "model"

    def test_vfolder_usage_mode_data(self) -> None:
        assert VFolderUsageMode.DATA.value == "data"


class TestVFolderMetadataInfo:
    """Tests for VFolderMetadataInfo sub-model."""

    def test_creation(self) -> None:
        now = datetime.now(tz=UTC)
        info = VFolderMetadataInfo(
            name="my-folder",
            usage_mode=VFolderUsageMode.GENERAL,
            quota_scope_id="user:abc",
            created_at=now,
            last_used=None,
            cloneable=False,
        )
        assert info.name == "my-folder"
        assert info.last_used is None
        assert info.cloneable is False

    def test_round_trip(self) -> None:
        now = datetime.now(tz=UTC)
        info = VFolderMetadataInfo(
            name="test",
            usage_mode=VFolderUsageMode.MODEL,
            quota_scope_id=None,
            created_at=now,
            last_used=now,
            cloneable=True,
        )
        restored = VFolderMetadataInfo.model_validate_json(info.model_dump_json())
        assert restored.name == info.name
        assert restored.usage_mode == VFolderUsageMode.MODEL
        assert restored.cloneable is True


class TestVFolderAccessControlInfo:
    """Tests for VFolderAccessControlInfo sub-model."""

    def test_creation(self) -> None:
        info = VFolderAccessControlInfo(
            permission=VFolderPermissionField.READ_WRITE,
            ownership_type=VFolderOwnershipTypeField.USER,
        )
        assert info.permission == VFolderPermissionField.READ_WRITE

    def test_round_trip(self) -> None:
        info = VFolderAccessControlInfo(
            permission=VFolderPermissionField.READ_ONLY,
            ownership_type=VFolderOwnershipTypeField.GROUP,
        )
        restored = VFolderAccessControlInfo.model_validate_json(info.model_dump_json())
        assert restored.permission == VFolderPermissionField.READ_ONLY
        assert restored.ownership_type == VFolderOwnershipTypeField.GROUP


class TestVFolderOwnershipInfo:
    """Tests for VFolderOwnershipInfo sub-model."""

    def test_creation_with_all_none(self) -> None:
        info = VFolderOwnershipInfo(user_id=None, project_id=None, creator_email=None)
        assert info.user_id is None
        assert info.project_id is None
        assert info.creator_email is None

    def test_creation_with_values(self) -> None:
        uid = uuid4()
        info = VFolderOwnershipInfo(user_id=uid, project_id=None, creator_email="user@example.com")
        assert info.user_id == uid
        assert info.creator_email == "user@example.com"


class TestVFolderUsageInfo:
    """Tests for VFolderUsageInfo sub-model."""

    def test_creation(self) -> None:
        info = VFolderUsageInfo(
            num_files=10,
            used_bytes=BinarySizeInfo(value=1024, display="1024"),
            max_size=None,
            max_files=1000,
        )
        assert info.num_files == 10
        assert info.max_size is None

    def test_round_trip(self) -> None:
        info = VFolderUsageInfo(
            num_files=5,
            used_bytes=BinarySizeInfo(value=512, display="512"),
            max_size=BinarySizeInfo(value=1048576, display="1m"),
            max_files=500,
        )
        restored = VFolderUsageInfo.model_validate_json(info.model_dump_json())
        assert restored.num_files == 5
        assert restored.max_size is not None
        assert restored.max_size.value == 1048576
