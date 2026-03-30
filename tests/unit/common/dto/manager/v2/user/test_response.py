"""Tests for ai.backend.common.dto.manager.v2.user.response module."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from ai.backend.common.dto.manager.pagination import PaginationInfo
from ai.backend.common.dto.manager.v2.user.response import (
    DeleteUserPayload,
    EntityTimestamps,
    PurgeUserPayload,
    SearchUsersPayload,
    UserBasicInfo,
    UserContainerSettings,
    UserNode,
    UserOrganizationInfo,
    UserPayload,
    UserSecurityInfo,
    UserStatusInfo,
)
from ai.backend.common.dto.manager.v2.user.types import UserRole, UserStatus


def make_user_node(user_id: uuid.UUID | None = None) -> UserNode:
    """Helper to create a valid UserNode for testing."""
    if user_id is None:
        user_id = uuid.uuid4()
    now = datetime.now(tz=UTC)
    return UserNode(
        id=user_id,
        basic_info=UserBasicInfo(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            description=None,
        ),
        status=UserStatusInfo(
            status=UserStatus.ACTIVE,
            status_info=None,
            need_password_change=False,
        ),
        organization=UserOrganizationInfo(
            domain_name="default",
            role=UserRole.USER,
            resource_policy="default",
            main_access_key=None,
        ),
        security=UserSecurityInfo(
            allowed_client_ip=None,
            totp_activated=False,
            totp_activated_at=None,
            sudo_session_enabled=False,
        ),
        container=UserContainerSettings(
            container_uid=None,
            container_main_gid=None,
            container_gids=None,
        ),
        timestamps=EntityTimestamps(
            created_at=now,
            modified_at=now,
        ),
    )


class TestUserBasicInfo:
    """Tests for UserBasicInfo sub-model."""

    def test_creation_with_required_fields(self) -> None:
        info = UserBasicInfo(email="user@example.com")
        assert info.email == "user@example.com"
        assert info.username is None
        assert info.full_name is None
        assert info.description is None

    def test_creation_with_all_fields(self) -> None:
        info = UserBasicInfo(
            username="user",
            email="user@example.com",
            full_name="Full Name",
            description="A user",
        )
        assert info.username == "user"
        assert info.full_name == "Full Name"
        assert info.description == "A user"

    def test_round_trip(self) -> None:
        info = UserBasicInfo(username="u", email="u@e.com", full_name="U")
        json_data = info.model_dump_json()
        restored = UserBasicInfo.model_validate_json(json_data)
        assert restored.username == "u"
        assert restored.email == "u@e.com"
        assert restored.full_name == "U"


class TestUserStatusInfo:
    """Tests for UserStatusInfo sub-model."""

    def test_creation_with_status(self) -> None:
        info = UserStatusInfo(status=UserStatus.ACTIVE)
        assert info.status == UserStatus.ACTIVE
        assert info.status_info is None
        assert info.need_password_change is None

    def test_creation_with_all_fields(self) -> None:
        info = UserStatusInfo(
            status=UserStatus.INACTIVE,
            status_info="Account suspended",
            need_password_change=True,
        )
        assert info.status == UserStatus.INACTIVE
        assert info.status_info == "Account suspended"
        assert info.need_password_change is True

    def test_round_trip(self) -> None:
        info = UserStatusInfo(status=UserStatus.DELETED, status_info="Deleted by admin")
        json_data = info.model_dump_json()
        restored = UserStatusInfo.model_validate_json(json_data)
        assert restored.status == UserStatus.DELETED
        assert restored.status_info == "Deleted by admin"


class TestUserOrganizationInfo:
    """Tests for UserOrganizationInfo sub-model."""

    def test_creation_with_required_fields(self) -> None:
        info = UserOrganizationInfo(resource_policy="default")
        assert info.resource_policy == "default"
        assert info.domain_name is None
        assert info.role is None
        assert info.main_access_key is None

    def test_creation_with_all_fields(self) -> None:
        info = UserOrganizationInfo(
            domain_name="test",
            role=UserRole.ADMIN,
            resource_policy="admin-policy",
            main_access_key="AKIAIOSFODNN7EXAMPLE",
        )
        assert info.domain_name == "test"
        assert info.role == UserRole.ADMIN
        assert info.main_access_key == "AKIAIOSFODNN7EXAMPLE"

    def test_round_trip(self) -> None:
        info = UserOrganizationInfo(
            domain_name="default",
            role=UserRole.USER,
            resource_policy="default",
        )
        json_data = info.model_dump_json()
        restored = UserOrganizationInfo.model_validate_json(json_data)
        assert restored.domain_name == "default"
        assert restored.role == UserRole.USER


class TestUserSecurityInfo:
    """Tests for UserSecurityInfo sub-model."""

    def test_creation_with_required_fields(self) -> None:
        info = UserSecurityInfo(sudo_session_enabled=False)
        assert info.sudo_session_enabled is False
        assert info.allowed_client_ip is None
        assert info.totp_activated is None
        assert info.totp_activated_at is None

    def test_creation_with_all_fields(self) -> None:
        now = datetime.now(tz=UTC)
        info = UserSecurityInfo(
            allowed_client_ip=["192.168.1.0/24", "10.0.0.1"],
            totp_activated=True,
            totp_activated_at=now,
            sudo_session_enabled=True,
        )
        assert info.allowed_client_ip == ["192.168.1.0/24", "10.0.0.1"]
        assert info.totp_activated is True
        assert info.sudo_session_enabled is True

    def test_round_trip(self) -> None:
        info = UserSecurityInfo(
            allowed_client_ip=["192.168.1.1"],
            totp_activated=False,
            sudo_session_enabled=True,
        )
        json_data = info.model_dump_json()
        restored = UserSecurityInfo.model_validate_json(json_data)
        assert restored.allowed_client_ip == ["192.168.1.1"]
        assert restored.sudo_session_enabled is True


class TestUserContainerSettings:
    """Tests for UserContainerSettings sub-model."""

    def test_all_none_defaults(self) -> None:
        settings = UserContainerSettings()
        assert settings.container_uid is None
        assert settings.container_main_gid is None
        assert settings.container_gids is None

    def test_creation_with_values(self) -> None:
        settings = UserContainerSettings(
            container_uid=1000,
            container_main_gid=1000,
            container_gids=[100, 200, 300],
        )
        assert settings.container_uid == 1000
        assert settings.container_main_gid == 1000
        assert settings.container_gids == [100, 200, 300]

    def test_round_trip(self) -> None:
        settings = UserContainerSettings(container_uid=1000, container_main_gid=1001)
        json_data = settings.model_dump_json()
        restored = UserContainerSettings.model_validate_json(json_data)
        assert restored.container_uid == 1000
        assert restored.container_main_gid == 1001


class TestEntityTimestamps:
    """Tests for EntityTimestamps sub-model."""

    def test_all_none_defaults(self) -> None:
        ts = EntityTimestamps()
        assert ts.created_at is None
        assert ts.modified_at is None

    def test_creation_with_datetime(self) -> None:
        now = datetime.now(tz=UTC)
        ts = EntityTimestamps(created_at=now, modified_at=now)
        assert ts.created_at == now
        assert ts.modified_at == now

    def test_round_trip(self) -> None:
        now = datetime.now(tz=UTC)
        ts = EntityTimestamps(created_at=now, modified_at=now)
        json_data = ts.model_dump_json()
        restored = EntityTimestamps.model_validate_json(json_data)
        assert restored.created_at is not None
        assert restored.modified_at is not None


class TestUserNode:
    """Tests for UserNode model creation with nested sub-models."""

    def test_creation_with_all_nested_groups(self) -> None:
        user_id = uuid.uuid4()
        node = make_user_node(user_id)
        assert node.id == user_id
        assert node.basic_info.email == "test@example.com"
        assert node.status.status == UserStatus.ACTIVE
        assert node.organization.resource_policy == "default"
        assert node.security.sudo_session_enabled is False
        assert node.container.container_uid is None
        assert node.timestamps.created_at is not None

    def test_id_is_uuid(self) -> None:
        node = make_user_node()
        assert isinstance(node.id, uuid.UUID)

    def test_nested_basic_info_fields(self) -> None:
        node = make_user_node()
        assert node.basic_info.username == "testuser"
        assert node.basic_info.full_name == "Test User"

    def test_nested_status_info_fields(self) -> None:
        node = make_user_node()
        assert node.status.status == UserStatus.ACTIVE
        assert node.status.need_password_change is False

    def test_nested_organization_info_fields(self) -> None:
        node = make_user_node()
        assert node.organization.domain_name == "default"
        assert node.organization.role == UserRole.USER

    def test_nested_security_info_fields(self) -> None:
        node = make_user_node()
        assert node.security.totp_activated is False
        assert node.security.allowed_client_ip is None

    def test_round_trip_serialization(self) -> None:
        user_id = uuid.uuid4()
        node = make_user_node(user_id)
        json_str = node.model_dump_json()
        restored = UserNode.model_validate_json(json_str)
        assert restored.id == user_id
        assert restored.basic_info.email == "test@example.com"
        assert restored.status.status == UserStatus.ACTIVE
        assert restored.organization.domain_name == "default"
        assert restored.security.sudo_session_enabled is False

    def test_serialized_json_has_nested_structure(self) -> None:
        node = make_user_node()
        data = json.loads(node.model_dump_json())
        assert "basic_info" in data
        assert "status" in data
        assert "organization" in data
        assert "security" in data
        assert "container" in data
        assert "timestamps" in data
        assert "email" in data["basic_info"]


class TestUserPayload:
    """Tests for UserPayload model."""

    def test_creation_with_user_node(self) -> None:
        node = make_user_node()
        payload = UserPayload(user=node)
        assert payload.user.basic_info.email == "test@example.com"

    def test_round_trip(self) -> None:
        user_id = uuid.uuid4()
        node = make_user_node(user_id)
        payload = UserPayload(user=node)
        json_str = payload.model_dump_json()
        restored = UserPayload.model_validate_json(json_str)
        assert restored.user.id == user_id
        assert restored.user.basic_info.email == "test@example.com"


class TestSearchUsersPayload:
    """Tests for SearchUsersPayload model."""

    def test_empty_items(self) -> None:
        payload = SearchUsersPayload(
            items=[],
            pagination=PaginationInfo(total=0, offset=0, limit=20),
        )
        assert payload.items == []
        assert payload.pagination.total == 0

    def test_with_items(self) -> None:
        nodes = [make_user_node(), make_user_node()]
        payload = SearchUsersPayload(
            items=nodes,
            pagination=PaginationInfo(total=2, offset=0, limit=20),
        )
        assert len(payload.items) == 2
        assert payload.pagination.total == 2

    def test_round_trip(self) -> None:
        user_id = uuid.uuid4()
        node = make_user_node(user_id)
        payload = SearchUsersPayload(
            items=[node],
            pagination=PaginationInfo(total=1, offset=0, limit=10),
        )
        json_str = payload.model_dump_json()
        restored = SearchUsersPayload.model_validate_json(json_str)
        assert len(restored.items) == 1
        assert restored.items[0].id == user_id
        assert restored.pagination.total == 1

    def test_pagination_limit_none(self) -> None:
        payload = SearchUsersPayload(
            items=[],
            pagination=PaginationInfo(total=0, offset=0, limit=None),
        )
        assert payload.pagination.limit is None


class TestDeleteUserPayload:
    """Tests for DeleteUserPayload model."""

    def test_success_true(self) -> None:
        payload = DeleteUserPayload(success=True)
        assert payload.success is True

    def test_success_false(self) -> None:
        payload = DeleteUserPayload(success=False)
        assert payload.success is False

    def test_round_trip(self) -> None:
        payload = DeleteUserPayload(success=True)
        json_str = payload.model_dump_json()
        restored = DeleteUserPayload.model_validate_json(json_str)
        assert restored.success is True


class TestPurgeUserPayload:
    """Tests for PurgeUserPayload model."""

    def test_success_true(self) -> None:
        payload = PurgeUserPayload(success=True)
        assert payload.success is True

    def test_success_false(self) -> None:
        payload = PurgeUserPayload(success=False)
        assert payload.success is False

    def test_round_trip(self) -> None:
        payload = PurgeUserPayload(success=False)
        json_str = payload.model_dump_json()
        restored = PurgeUserPayload.model_validate_json(json_str)
        assert restored.success is False
