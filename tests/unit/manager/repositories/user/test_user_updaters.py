"""Unit tests for UserUpdaterSpec."""

from __future__ import annotations

import pytest

from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.repositories.user.updaters import UserUpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


class TestUserUpdaterSpecBuildValues:
    """Tests for UserUpdaterSpec.build_values() method."""

    def test_build_values_with_all_nop_returns_empty_dict(self) -> None:
        """When all fields are nop, build_values should return empty dict."""
        spec = UserUpdaterSpec()

        result = spec.build_values()

        assert result == {}

    def test_build_values_with_status_set_includes_status(self) -> None:
        """When status is explicitly set, it should be included."""
        spec = UserUpdaterSpec(
            status=OptionalState.update(UserStatus.ACTIVE),
        )

        result = spec.build_values()

        assert result == {"status": UserStatus.ACTIVE}

    def test_build_values_with_is_active_true_sets_status_active(self) -> None:
        """When is_active is True and status is nop, status should be ACTIVE."""
        spec = UserUpdaterSpec(
            is_active=OptionalState.update(True),
        )

        result = spec.build_values()

        assert result["is_active"] is True
        assert result["status"] == UserStatus.ACTIVE

    def test_build_values_with_is_active_false_sets_status_inactive(self) -> None:
        """When is_active is False and status is nop, status should be INACTIVE."""
        spec = UserUpdaterSpec(
            is_active=OptionalState.update(False),
        )

        result = spec.build_values()

        assert result["is_active"] is False
        assert result["status"] == UserStatus.INACTIVE

    def test_build_values_status_takes_precedence_over_is_active(self) -> None:
        """When both status and is_active are set, status takes precedence."""
        spec = UserUpdaterSpec(
            is_active=OptionalState.update(True),
            status=OptionalState.update(UserStatus.INACTIVE),
        )

        result = spec.build_values()

        assert result["is_active"] is True
        assert result["status"] == UserStatus.INACTIVE

    def test_build_values_with_username(self) -> None:
        """Test username field is included when set."""
        spec = UserUpdaterSpec(
            username=OptionalState.update("new_username"),
        )

        result = spec.build_values()

        assert result["username"] == "new_username"
        # status should not be included since both status and is_active are nop
        assert "status" not in result

    def test_build_values_with_role(self) -> None:
        """Test role field is included when set."""
        spec = UserUpdaterSpec(
            role=OptionalState.update(UserRole.ADMIN),
        )

        result = spec.build_values()

        assert result["role"] == UserRole.ADMIN
        assert "status" not in result

    def test_build_values_with_tristate_update(self) -> None:
        """Test TriState fields with update state."""
        spec = UserUpdaterSpec(
            allowed_client_ip=TriState.update(["192.168.1.1", "10.0.0.1"]),
            container_uid=TriState.update(1000),
        )

        result = spec.build_values()

        assert result["allowed_client_ip"] == ["192.168.1.1", "10.0.0.1"]
        assert result["container_uid"] == 1000

    def test_build_values_with_tristate_nullify(self) -> None:
        """Test TriState fields with nullify state sets value to None."""
        spec = UserUpdaterSpec(
            allowed_client_ip=TriState.nullify(),
            main_access_key=TriState.nullify(),
        )

        result = spec.build_values()

        assert result["allowed_client_ip"] is None
        assert result["main_access_key"] is None

    def test_build_values_with_tristate_nop(self) -> None:
        """Test TriState fields with nop state are not included."""
        spec = UserUpdaterSpec(
            allowed_client_ip=TriState.nop(),
            container_uid=TriState.nop(),
        )

        result = spec.build_values()

        assert "allowed_client_ip" not in result
        assert "container_uid" not in result

    def test_build_values_with_multiple_fields(self) -> None:
        """Test multiple fields are correctly included."""
        spec = UserUpdaterSpec(
            username=OptionalState.update("updated_user"),
            full_name=OptionalState.update("Updated Name"),
            description=OptionalState.update("Updated description"),
            role=OptionalState.update(UserRole.USER),
            status=OptionalState.update(UserStatus.ACTIVE),
            totp_activated=OptionalState.update(True),
            sudo_session_enabled=OptionalState.update(False),
        )

        result = spec.build_values()

        assert result["username"] == "updated_user"
        assert result["full_name"] == "Updated Name"
        assert result["description"] == "Updated description"
        assert result["role"] == UserRole.USER
        assert result["status"] == UserStatus.ACTIVE
        assert result["totp_activated"] is True
        assert result["sudo_session_enabled"] is False

    def test_build_values_with_container_gids(self) -> None:
        """Test container_gids TriState field."""
        spec = UserUpdaterSpec(
            container_gids=TriState.update([1000, 1001, 1002]),
        )

        result = spec.build_values()

        assert result["container_gids"] == [1000, 1001, 1002]


class TestUserUpdaterSpecGroupIds:
    """Tests for UserUpdaterSpec.group_ids_value property."""

    def test_group_ids_value_returns_none_when_nop(self) -> None:
        """group_ids_value should return None when group_ids is nop."""
        spec = UserUpdaterSpec()

        assert spec.group_ids_value is None

    def test_group_ids_value_returns_value_when_set(self) -> None:
        """group_ids_value should return the value when group_ids is set."""
        group_ids = ["group1", "group2", "group3"]
        spec = UserUpdaterSpec(
            group_ids=OptionalState.update(group_ids),
        )

        assert spec.group_ids_value == group_ids


class TestUserUpdaterSpecRowClass:
    """Tests for UserUpdaterSpec.row_class property."""

    def test_row_class_returns_user_row(self) -> None:
        """row_class should return UserRow."""
        from ai.backend.manager.models.user import UserRow

        spec = UserUpdaterSpec()

        assert spec.row_class is UserRow
