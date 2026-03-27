"""Tests for ai.backend.common.dto.manager.v2.vfolder.types module."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from ai.backend.common.dto.manager.v2.vfolder.types import (
    OrderDirection,
    VFolderBasicInfo,
    VFolderInvitationState,
    VFolderOperationStatusField,
    VFolderOrderField,
    VFolderOwnerInfo,
    VFolderOwnershipTypeField,
    VFolderPermissionField,
    VFolderPermissionInfo,
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


class TestVFolderBasicInfo:
    """Tests for VFolderBasicInfo sub-model."""

    def test_creation(self) -> None:
        now = datetime.now(tz=UTC)
        info = VFolderBasicInfo(
            id=uuid4(),
            name="my-folder",
            host="nfs01",
            quota_scope_id="user:abc",
            usage_mode=VFolderUsageMode.GENERAL,
            status=VFolderOperationStatusField.READY,
            created_at=now,
            last_used=None,
        )
        assert info.name == "my-folder"
        assert info.last_used is None

    def test_round_trip(self) -> None:
        now = datetime.now(tz=UTC)
        info = VFolderBasicInfo(
            id=uuid4(),
            name="test",
            host="nfs01",
            quota_scope_id=None,
            usage_mode=VFolderUsageMode.MODEL,
            status=VFolderOperationStatusField.READY,
            created_at=now,
            last_used=now,
        )
        restored = VFolderBasicInfo.model_validate_json(info.model_dump_json())
        assert restored.name == info.name
        assert restored.usage_mode == VFolderUsageMode.MODEL


class TestVFolderPermissionInfo:
    """Tests for VFolderPermissionInfo sub-model."""

    def test_creation(self) -> None:
        info = VFolderPermissionInfo(
            permission=VFolderPermissionField.READ_WRITE,
            ownership_type=VFolderOwnershipTypeField.USER,
            is_owner=True,
            cloneable=False,
        )
        assert info.is_owner is True
        assert info.cloneable is False

    def test_round_trip(self) -> None:
        info = VFolderPermissionInfo(
            permission=VFolderPermissionField.READ_ONLY,
            ownership_type=VFolderOwnershipTypeField.GROUP,
            is_owner=False,
            cloneable=True,
        )
        restored = VFolderPermissionInfo.model_validate_json(info.model_dump_json())
        assert restored.permission == VFolderPermissionField.READ_ONLY
        assert restored.ownership_type == VFolderOwnershipTypeField.GROUP


class TestVFolderOwnerInfo:
    """Tests for VFolderOwnerInfo sub-model."""

    def test_creation_with_all_none(self) -> None:
        info = VFolderOwnerInfo(user=None, group=None, creator=None)
        assert info.user is None
        assert info.group is None
        assert info.creator is None

    def test_creation_with_values(self) -> None:
        uid = uuid4()
        info = VFolderOwnerInfo(user=uid, group=None, creator="user@example.com")
        assert info.user == uid
        assert info.creator == "user@example.com"


class TestVFolderUsageInfo:
    """Tests for VFolderUsageInfo sub-model."""

    def test_creation(self) -> None:
        info = VFolderUsageInfo(num_files=10, used_bytes=1024, max_size=None, max_files=1000)
        assert info.num_files == 10
        assert info.max_size is None

    def test_round_trip(self) -> None:
        info = VFolderUsageInfo(num_files=5, used_bytes=512, max_size=1048576, max_files=500)
        restored = VFolderUsageInfo.model_validate_json(info.model_dump_json())
        assert restored.num_files == 5
        assert restored.max_size == 1048576
