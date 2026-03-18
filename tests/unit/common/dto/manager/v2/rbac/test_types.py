"""Tests for ai.backend.common.dto.manager.v2.rbac.types module."""

from __future__ import annotations

import json

from ai.backend.common.data.permission.types import (
    EntityType,
    OperationType,
    RoleSource,
    RoleStatus,
)
from ai.backend.common.dto.manager.v2.rbac.types import EntityType as ExportedEntityType
from ai.backend.common.dto.manager.v2.rbac.types import OperationType as ExportedOperationType
from ai.backend.common.dto.manager.v2.rbac.types import (
    OrderDirection,
    PermissionSummary,
    RoleOrderField,
)
from ai.backend.common.dto.manager.v2.rbac.types import RoleSource as ExportedRoleSource
from ai.backend.common.dto.manager.v2.rbac.types import RoleStatus as ExportedRoleStatus


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "asc"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "desc"

    def test_all_values_are_strings(self) -> None:
        for member in OrderDirection:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(OrderDirection)
        assert len(members) == 2

    def test_from_string_asc(self) -> None:
        assert OrderDirection("asc") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("desc") is OrderDirection.DESC


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

    def test_operation_type_is_same_object(self) -> None:
        assert ExportedOperationType is OperationType

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
        assert ExportedEntityType.USER.value == "user"

    def test_entity_type_role_value(self) -> None:
        assert ExportedEntityType.ROLE.value == "role"

    def test_operation_type_create_value(self) -> None:
        assert ExportedOperationType.CREATE.value == "create"

    def test_operation_type_read_value(self) -> None:
        assert ExportedOperationType.READ.value == "read"


class TestPermissionSummaryCreation:
    """Tests for PermissionSummary Pydantic model creation."""

    def test_basic_creation(self) -> None:
        perm = PermissionSummary(
            entity_type=EntityType.ROLE,
            operation=OperationType.READ,
        )
        assert perm.entity_type == EntityType.ROLE
        assert perm.operation == OperationType.READ

    def test_creation_with_user_entity_type(self) -> None:
        perm = PermissionSummary(
            entity_type=EntityType.USER,
            operation=OperationType.CREATE,
        )
        assert perm.entity_type == EntityType.USER
        assert perm.operation == OperationType.CREATE

    def test_creation_with_update_operation(self) -> None:
        perm = PermissionSummary(
            entity_type=EntityType.SESSION,
            operation=OperationType.UPDATE,
        )
        assert perm.entity_type == EntityType.SESSION
        assert perm.operation == OperationType.UPDATE

    def test_creation_with_soft_delete_operation(self) -> None:
        perm = PermissionSummary(
            entity_type=EntityType.VFOLDER,
            operation=OperationType.SOFT_DELETE,
        )
        assert perm.entity_type == EntityType.VFOLDER
        assert perm.operation == OperationType.SOFT_DELETE

    def test_creation_with_hard_delete_operation(self) -> None:
        perm = PermissionSummary(
            entity_type=EntityType.IMAGE,
            operation=OperationType.HARD_DELETE,
        )
        assert perm.entity_type == EntityType.IMAGE
        assert perm.operation == OperationType.HARD_DELETE

    def test_creation_from_string_values(self) -> None:
        perm = PermissionSummary.model_validate({
            "entity_type": "role",
            "operation": "read",
        })
        assert perm.entity_type == EntityType.ROLE
        assert perm.operation == OperationType.READ

    def test_creation_from_string_values_create(self) -> None:
        perm = PermissionSummary.model_validate({
            "entity_type": "user",
            "operation": "create",
        })
        assert perm.entity_type == EntityType.USER
        assert perm.operation == OperationType.CREATE


class TestPermissionSummarySerialization:
    """Tests for PermissionSummary serialization and deserialization."""

    def test_model_dump(self) -> None:
        perm = PermissionSummary(
            entity_type=EntityType.ROLE,
            operation=OperationType.READ,
        )
        data = perm.model_dump()
        assert data["entity_type"] == EntityType.ROLE
        assert data["operation"] == OperationType.READ

    def test_model_dump_json(self) -> None:
        perm = PermissionSummary(
            entity_type=EntityType.ROLE,
            operation=OperationType.READ,
        )
        json_str = perm.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["entity_type"] == "role"
        assert parsed["operation"] == "read"

    def test_model_dump_json_with_enum_values(self) -> None:
        perm = PermissionSummary(
            entity_type=EntityType.USER,
            operation=OperationType.CREATE,
        )
        json_str = perm.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["entity_type"] == "user"
        assert parsed["operation"] == "create"

    def test_serialization_round_trip(self) -> None:
        perm = PermissionSummary(
            entity_type=EntityType.ROLE,
            operation=OperationType.READ,
        )
        json_str = perm.model_dump_json()
        restored = PermissionSummary.model_validate_json(json_str)
        assert restored.entity_type == perm.entity_type
        assert restored.operation == perm.operation

    def test_serialization_round_trip_with_grant_operation(self) -> None:
        perm = PermissionSummary(
            entity_type=EntityType.SESSION,
            operation=OperationType.GRANT_ALL,
        )
        json_str = perm.model_dump_json()
        restored = PermissionSummary.model_validate_json(json_str)
        assert restored.entity_type == perm.entity_type
        assert restored.operation == perm.operation

    def test_json_schema_has_properties(self) -> None:
        schema = PermissionSummary.model_json_schema()
        assert "properties" in schema
        assert "entity_type" in schema["properties"]
        assert "operation" in schema["properties"]

    def test_model_dump_preserves_enum_instances(self) -> None:
        perm = PermissionSummary(
            entity_type=EntityType.DOMAIN,
            operation=OperationType.UPDATE,
        )
        data = perm.model_dump()
        # model_dump returns enum instances by default
        assert data["entity_type"] == EntityType.DOMAIN
        assert data["operation"] == OperationType.UPDATE

    def test_list_of_permission_summaries_serialization(self) -> None:
        permissions = [
            PermissionSummary(
                entity_type=EntityType.ROLE,
                operation=OperationType.READ,
            ),
            PermissionSummary(
                entity_type=EntityType.USER,
                operation=OperationType.CREATE,
            ),
        ]
        serialized = [p.model_dump_json() for p in permissions]
        restored = [PermissionSummary.model_validate_json(s) for s in serialized]

        assert len(restored) == 2
        assert restored[0].entity_type == EntityType.ROLE
        assert restored[0].operation == OperationType.READ
        assert restored[1].entity_type == EntityType.USER
        assert restored[1].operation == OperationType.CREATE
