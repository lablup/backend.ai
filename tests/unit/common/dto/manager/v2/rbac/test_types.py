"""Tests for ai.backend.common.dto.manager.v2.rbac.types module."""

from __future__ import annotations

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.permission.types import (
    RoleSource,
    RoleStatus,
)
from ai.backend.common.dto.manager.v2.rbac.types import EntityType as ExportedEntityType
from ai.backend.common.dto.manager.v2.rbac.types import (
    OrderDirection,
    RoleOrderField,
)
from ai.backend.common.dto.manager.v2.rbac.types import RoleSource as ExportedRoleSource
from ai.backend.common.dto.manager.v2.rbac.types import RoleStatus as ExportedRoleStatus


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "ASC"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "DESC"

    def test_all_values_are_strings(self) -> None:
        for member in OrderDirection:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(OrderDirection)
        assert len(members) == 2

    def test_from_string_asc(self) -> None:
        assert OrderDirection("ASC") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("DESC") is OrderDirection.DESC


class TestRoleOrderField:
    """Tests for RoleOrderField enum."""

    def test_name_value(self) -> None:
        assert RoleOrderField.NAME.value == "name"

    def test_created_at_value(self) -> None:
        assert RoleOrderField.CREATED_AT.value == "created_at"

    def test_updated_at_value(self) -> None:
        assert RoleOrderField.UPDATED_AT.value == "updated_at"

    def test_all_values_are_strings(self) -> None:
        for member in RoleOrderField:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(RoleOrderField)
        assert len(members) == 3

    def test_from_string_name(self) -> None:
        assert RoleOrderField("name") is RoleOrderField.NAME

    def test_from_string_created_at(self) -> None:
        assert RoleOrderField("created_at") is RoleOrderField.CREATED_AT

    def test_from_string_updated_at(self) -> None:
        assert RoleOrderField("updated_at") is RoleOrderField.UPDATED_AT


class TestReExportedEnums:
    """Tests verifying that enums are properly re-exported from types module."""

    def test_role_source_is_same_object(self) -> None:
        assert ExportedRoleSource is RoleSource

    def test_role_status_is_same_object(self) -> None:
        assert ExportedRoleStatus is RoleStatus

    def test_entity_type_is_same_object(self) -> None:
        assert ExportedEntityType is EntityType

    def test_role_source_custom_value(self) -> None:
        assert ExportedRoleSource.CUSTOM.value == "custom"

    def test_role_source_system_value(self) -> None:
        assert ExportedRoleSource.SYSTEM.value == "system"

    def test_role_status_active_value(self) -> None:
        assert ExportedRoleStatus.ACTIVE.value == "active"

    def test_role_status_inactive_value(self) -> None:
        assert ExportedRoleStatus.INACTIVE.value == "inactive"

    def test_role_status_deleted_value(self) -> None:
        assert ExportedRoleStatus.DELETED.value == "deleted"

    def test_entity_type_user_value(self) -> None:
        assert ExportedEntityType("user") == "user"

    def test_entity_type_role_value(self) -> None:
        assert ExportedEntityType("role") == "role"
