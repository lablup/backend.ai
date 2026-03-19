"""Tests for ai.backend.common.dto.manager.v2.user.types module."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.user.types import (
    OrderDirection,
    UserOrderField,
    UserRole,
    UserStatus,
)


class TestUserStatus:
    """Tests for UserStatus enum."""

    def test_active_value(self) -> None:
        assert UserStatus.ACTIVE.value == "active"

    def test_inactive_value(self) -> None:
        assert UserStatus.INACTIVE.value == "inactive"

    def test_deleted_value(self) -> None:
        assert UserStatus.DELETED.value == "deleted"

    def test_before_verification_value(self) -> None:
        assert UserStatus.BEFORE_VERIFICATION.value == "before-verification"

    def test_all_values_are_strings(self) -> None:
        for member in UserStatus:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        assert len(list(UserStatus)) == 4

    def test_from_string_active(self) -> None:
        assert UserStatus("active") is UserStatus.ACTIVE

    def test_from_string_inactive(self) -> None:
        assert UserStatus("inactive") is UserStatus.INACTIVE

    def test_from_string_deleted(self) -> None:
        assert UserStatus("deleted") is UserStatus.DELETED

    def test_from_string_before_verification(self) -> None:
        assert UserStatus("before-verification") is UserStatus.BEFORE_VERIFICATION


class TestUserRole:
    """Tests for UserRole enum."""

    def test_superadmin_value(self) -> None:
        assert UserRole.SUPERADMIN.value == "superadmin"

    def test_admin_value(self) -> None:
        assert UserRole.ADMIN.value == "admin"

    def test_user_value(self) -> None:
        assert UserRole.USER.value == "user"

    def test_monitor_value(self) -> None:
        assert UserRole.MONITOR.value == "monitor"

    def test_all_values_are_strings(self) -> None:
        for member in UserRole:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        assert len(list(UserRole)) == 4

    def test_from_string_superadmin(self) -> None:
        assert UserRole("superadmin") is UserRole.SUPERADMIN

    def test_from_string_admin(self) -> None:
        assert UserRole("admin") is UserRole.ADMIN

    def test_from_string_user(self) -> None:
        assert UserRole("user") is UserRole.USER

    def test_from_string_monitor(self) -> None:
        assert UserRole("monitor") is UserRole.MONITOR


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "asc"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "desc"

    def test_enum_members_count(self) -> None:
        assert len(list(OrderDirection)) == 2

    def test_from_string_asc(self) -> None:
        assert OrderDirection("asc") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("desc") is OrderDirection.DESC


class TestUserOrderField:
    """Tests for UserOrderField enum."""

    def test_created_at_value(self) -> None:
        assert UserOrderField.CREATED_AT.value == "created_at"

    def test_modified_at_value(self) -> None:
        assert UserOrderField.MODIFIED_AT.value == "modified_at"

    def test_username_value(self) -> None:
        assert UserOrderField.USERNAME.value == "username"

    def test_email_value(self) -> None:
        assert UserOrderField.EMAIL.value == "email"

    def test_status_value(self) -> None:
        assert UserOrderField.STATUS.value == "status"

    def test_domain_name_value(self) -> None:
        assert UserOrderField.DOMAIN_NAME.value == "domain_name"

    def test_enum_members_count(self) -> None:
        assert len(list(UserOrderField)) == 7

    def test_all_values_are_strings(self) -> None:
        for member in UserOrderField:
            assert isinstance(member.value, str)

    def test_from_string_username(self) -> None:
        assert UserOrderField("username") is UserOrderField.USERNAME

    def test_from_string_email(self) -> None:
        assert UserOrderField("email") is UserOrderField.EMAIL
