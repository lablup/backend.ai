"""Tests for ai.backend.manager.data.user.types module — group membership."""

from __future__ import annotations

from uuid import UUID, uuid4

from ai.backend.common.data.user.types import UserRole as DataUserRole
from ai.backend.manager.data.user.types import UserData, UserGroupMembership


def _create_user_data(
    user_id: UUID | None = None,
    groups: list[UserGroupMembership] | None = None,
) -> UserData:
    uid = user_id or uuid4()
    return UserData(
        id=uid,
        uuid=uid,
        username="testuser",
        email="test@example.com",
        need_password_change=False,
        full_name="Test User",
        description=None,
        is_active=True,
        status="active",
        status_info=None,
        created_at=None,
        modified_at=None,
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


class TestUserGroupMembership:
    """Tests for UserGroupMembership dataclass."""

    def test_instantiation(self) -> None:
        group_id = uuid4()
        membership = UserGroupMembership(id=group_id, name="researchers")
        assert membership.id == group_id
        assert membership.name == "researchers"

    def test_different_instances_are_independent(self) -> None:
        id1 = uuid4()
        id2 = uuid4()
        m1 = UserGroupMembership(id=id1, name="group-a")
        m2 = UserGroupMembership(id=id2, name="group-b")
        assert m1.id != m2.id
        assert m1.name != m2.name


class TestUserDataGroups:
    """Tests for the groups field on UserData."""

    def test_groups_defaults_to_empty_list(self) -> None:
        data = _create_user_data()
        assert data.groups == []

    def test_groups_with_populated_list(self) -> None:
        group_id = uuid4()
        membership = UserGroupMembership(id=group_id, name="my-group")
        data = _create_user_data(groups=[membership])
        assert len(data.groups) == 1
        assert data.groups[0].id == group_id
        assert data.groups[0].name == "my-group"
