"""Tests for v2 UserAdapter._user_data_to_node conversion."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from ai.backend.common.data.user.types import UserRole as DataUserRole
from ai.backend.common.dto.manager.v2.user.response import UserGroupMembershipDTO
from ai.backend.manager.api.adapters.user import UserAdapter
from ai.backend.manager.data.user.types import UserData, UserGroupMembership


def _create_user_data(
    user_id: UUID | None = None,
    groups: list[UserGroupMembership] | None = None,
) -> UserData:
    """Create a minimal UserData for testing adapter conversion."""
    now = datetime.now(tz=UTC)
    return UserData(
        id=user_id or uuid4(),
        uuid=user_id or uuid4(),
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
        groups=groups if groups is not None else [],
    )


class TestUserDataToNodeGroups:
    """Tests for _user_data_to_node group membership mapping."""

    def test_empty_groups_produces_empty_list(self) -> None:
        """UserData with no groups should produce UserNode.groups == []."""
        data = _create_user_data(groups=[])
        node = UserAdapter._user_data_to_node(data)
        assert node.groups == []

    def test_populated_groups_mapped_correctly(self) -> None:
        """UserData with group memberships should produce correctly mapped UserNode.groups."""
        group_id_1 = uuid4()
        group_id_2 = uuid4()
        groups = [
            UserGroupMembership(id=group_id_1, name="researchers"),
            UserGroupMembership(id=group_id_2, name="developers"),
        ]
        data = _create_user_data(groups=groups)
        node = UserAdapter._user_data_to_node(data)

        assert len(node.groups) == 2
        assert isinstance(node.groups[0], UserGroupMembershipDTO)
        assert isinstance(node.groups[1], UserGroupMembershipDTO)
        assert node.groups[0].id == str(group_id_1)
        assert node.groups[0].name == "researchers"
        assert node.groups[1].id == str(group_id_2)
        assert node.groups[1].name == "developers"

    def test_single_group_mapped_correctly(self) -> None:
        """UserData with a single group membership maps to a single-element list."""
        group_id = uuid4()
        groups = [UserGroupMembership(id=group_id, name="admins")]
        data = _create_user_data(groups=groups)
        node = UserAdapter._user_data_to_node(data)

        assert len(node.groups) == 1
        assert node.groups[0].id == str(group_id)
        assert node.groups[0].name == "admins"
