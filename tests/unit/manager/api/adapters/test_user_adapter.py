"""Tests for v2 UserAdapter._user_data_to_node and _user_data_to_detail_node conversion."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from ai.backend.common.data.user.types import UserRole as DataUserRole
from ai.backend.common.dto.manager.v2.user.response import (
    UserDetailNode,
    UserGroupMembershipInfo,
    UserNode,
)
from ai.backend.manager.api.adapters.user import UserAdapter
from ai.backend.manager.data.user.types import UserData, UserGroupMembership


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
    )


class TestUserDataToNode:
    """Tests for _user_data_to_node conversion."""

    def test_returns_user_node(self) -> None:
        data = _create_user_data()
        node = UserAdapter._user_data_to_node(data)
        assert isinstance(node, UserNode)
        assert not isinstance(node, UserDetailNode)

    def test_does_not_have_groups(self) -> None:
        data = _create_user_data()
        node = UserAdapter._user_data_to_node(data)
        assert not hasattr(node, "groups") or "groups" not in node.model_fields


class TestUserDataToDetailNodeGroups:
    """Tests for _user_data_to_detail_node group membership mapping."""

    def test_no_groups_produces_empty_list(self) -> None:
        data = _create_user_data()
        node = UserAdapter._user_data_to_detail_node(data)
        assert isinstance(node, UserDetailNode)
        assert node.groups == []

    def test_populated_groups_mapped_correctly(self) -> None:
        group_id_1 = uuid4()
        group_id_2 = uuid4()
        groups = [
            UserGroupMembership(id=group_id_1, name="researchers"),
            UserGroupMembership(id=group_id_2, name="developers"),
        ]
        data = _create_user_data()
        node = UserAdapter._user_data_to_detail_node(data, groups=groups)

        assert len(node.groups) == 2
        assert isinstance(node.groups[0], UserGroupMembershipInfo)
        assert isinstance(node.groups[1], UserGroupMembershipInfo)
        assert node.groups[0].id == group_id_1
        assert node.groups[0].name == "researchers"
        assert node.groups[1].id == group_id_2
        assert node.groups[1].name == "developers"

    def test_single_group_mapped_correctly(self) -> None:
        group_id = uuid4()
        groups = [UserGroupMembership(id=group_id, name="admins")]
        data = _create_user_data()
        node = UserAdapter._user_data_to_detail_node(data, groups=groups)

        assert len(node.groups) == 1
        assert node.groups[0].id == group_id
        assert node.groups[0].name == "admins"

    def test_detail_node_is_subclass_of_user_node(self) -> None:
        data = _create_user_data()
        node = UserAdapter._user_data_to_detail_node(data)
        assert isinstance(node, UserNode)
