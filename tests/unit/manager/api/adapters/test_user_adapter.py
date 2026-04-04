"""Tests for v2 UserAdapter._user_data_to_node conversion."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from ai.backend.common.data.user.types import UserRole as DataUserRole
from ai.backend.manager.api.adapters.user import UserAdapter
from ai.backend.manager.data.user.types import UserData


def _create_user_data(
    user_id: UUID | None = None,
) -> UserData:
    """Create a minimal UserData for testing adapter conversion."""
    now = datetime.now(tz=UTC)
    effective_id = user_id or uuid4()
    return UserData(
        id=effective_id,
        uuid=effective_id,
        username="testuser",
        email="test@example.com",
        need_password_change=False,
        full_name="Test User",
        description="A test user",
        is_active=True,
        status="active",
        status_info=None,
        created_at=now,
        modified_at=now,
        domain_name="default",
        role=DataUserRole.USER,
        resource_policy="default",
        allowed_client_ip=None,
        totp_activated=False,
        totp_activated_at=None,
        sudo_session_enabled=False,
        main_access_key=None,
        container_uid=None,
        container_main_gid=None,
        container_gids=None,
        integration_name="ext-test-system",
    )


class TestUserDataToNode:
    """Tests for _user_data_to_node conversion."""

    def test_basic_fields_mapped_correctly(self) -> None:
        """UserData fields should map to UserNode sub-models."""
        user_id = uuid4()
        data = _create_user_data(user_id=user_id)
        node = UserAdapter._user_data_to_node(data)

        assert node.id == user_id
        assert node.basic_info.username == "testuser"
        assert node.basic_info.email == "test@example.com"
        assert node.basic_info.full_name == "Test User"
        assert node.basic_info.description == "A test user"
        assert node.basic_info.integration_name == "ext-test-system"
        assert node.organization.domain_name == "default"
        assert node.organization.resource_policy == "default"
        assert node.status.need_password_change is False
        assert node.security.totp_activated is False
        assert node.container.container_uid is None

    def test_node_has_no_groups_field(self) -> None:
        """UserNode should not have a groups field."""
        data = _create_user_data()
        node = UserAdapter._user_data_to_node(data)
        assert not hasattr(node, "groups")
